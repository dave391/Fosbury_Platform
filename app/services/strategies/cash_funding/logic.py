import logging
import math
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import Strategy, StrategyPosition
from core.enums import StrategyStatus
from app.services.strategies.base import StrategyAdapter
from app.services.strategies.cash_funding.rules import (
    STRATEGY_KEY,
    STRATEGY_NAME,
    MIN_CAPITAL_USD,
    FEE_BUFFER,
    get_exchange_rules,
)

logger = logging.getLogger(__name__)


async def resolve_symbol(exchange, market_id: str) -> str:
    if not exchange.markets:
        await exchange.load_markets()
    market = exchange.markets_by_id.get(market_id)
    if market:
        if isinstance(market, list):
            market = market[0]
        return market["symbol"]
    if market_id in exchange.markets:
        return market_id
    raise ValueError(f"Market {market_id} not found")


def _exchange_id(exchange) -> str:
    return getattr(exchange, "id", "") or ""


def _get_rules(exchange_id: str) -> dict:
    return get_exchange_rules(exchange_id)


def _validate_asset(rules: dict, asset: str) -> None:
    allowed = rules.get("assets") or []
    if allowed and asset not in allowed:
        raise ValueError("Asset non disponibile per questo exchange.")


def _pick_market(markets, base: str, quote: str, market_type: str):
    candidates = [
        market for market in markets
        if market.get("base") == base
        and market.get("quote") == quote
        and market.get(market_type)
    ]
    if market_type == "swap":
        linear = [market for market in candidates if market.get("linear")]
        if linear:
            return linear[0]
    return candidates[0] if candidates else None


async def build_strategy_config(exchange, asset: str) -> dict:
    if not exchange.markets:
        await exchange.load_markets()
    exchange_id = _exchange_id(exchange)
    rules = _get_rules(exchange_id)
    _validate_asset(rules, asset)
    quote = rules.get("quote") or "USDC"
    aliases = rules.get("spot_asset_aliases") or {}
    spot_asset = aliases.get(asset, asset)
    markets = list(exchange.markets.values())
    spot_market = _pick_market(markets, spot_asset, quote, "spot")
    perp_market = _pick_market(markets, asset, quote, "swap")
    if not spot_market:
        spot_id = f"{spot_asset}_{quote}"
        spot_symbol = await resolve_symbol(exchange, spot_id)
        spot_market = exchange.markets.get(spot_symbol)
    if not perp_market:
        perp_id = f"{asset}_{quote}-PERPETUAL"
        perp_symbol = await resolve_symbol(exchange, perp_id)
        perp_market = exchange.markets.get(perp_symbol)
    if not spot_market or not perp_market:
        raise ValueError("Mercati spot/perp non disponibili per questa strategia.")
    perp_size_mode = "base"
    contract_size = perp_market.get("contractSize")
    forced_size_mode = rules.get("perp_size_mode") or "auto"
    if forced_size_mode == "auto":
        if perp_market.get("contract") and perp_market.get("linear") and contract_size:
            perp_size_mode = "contracts"
    else:
        perp_size_mode = forced_size_mode
    return {
        "exchange": exchange_id,
        "asset": asset,
        "quote": quote,
        "spot_asset": spot_asset,
        "spot_symbol": spot_market.get("symbol"),
        "perp_symbol": perp_market.get("symbol"),
        "spot_id": spot_market.get("id"),
        "perp_id": perp_market.get("id"),
        "perp_size_mode": perp_size_mode,
        "perp_contract_size": contract_size,
    }


async def ensure_strategy_config(exchange, asset: str, config: dict) -> dict:
    if config and config.get("spot_symbol") and config.get("perp_symbol"):
        return config
    return await build_strategy_config(exchange, asset)


async def fetch_usdc_balance(exchange, adapter) -> float:
    exchange_id = _exchange_id(exchange)
    rules = _get_rules(exchange_id)
    quote = rules.get("quote") or "USDC"
    return await adapter.fetch_quote_balance(exchange, quote)


async def get_last_price(exchange, symbol: str) -> float:
    ticker = await exchange.fetch_ticker(symbol)
    price = ticker.get("last") or ticker.get("close") or ticker.get("average")
    if price is None:
        raise ValueError(f"Price not available for {symbol}")
    return float(price)


def amount_to_precision(exchange, symbol: str, amount: float) -> float:
    precise = exchange.amount_to_precision(symbol, amount)
    return float(precise)


def _market_cost_step(exchange, symbol: str, price: float) -> float:
    market = exchange.markets.get(symbol) or {}
    limits = market.get("limits") or {}
    cost_min = (limits.get("cost") or {}).get("min")
    if cost_min:
        try:
            value = float(cost_min)
            if value > 0:
                return value
        except (TypeError, ValueError):
            pass
    precision = (market.get("precision") or {}).get("amount")
    if precision is None:
        return 0.0
    try:
        precision_value = float(precision)
    except (TypeError, ValueError):
        return 0.0
    if precision_value < 0:
        return 0.0
    if precision_value.is_integer():
        step_amount = 10 ** (-int(precision_value))
    else:
        step_amount = precision_value
    if price <= 0:
        return 0.0
    return step_amount * price


def _perp_notional_step(exchange, symbol: str, price: float) -> float:
    market = exchange.markets.get(symbol) or {}
    exchange_id = _exchange_id(exchange)
    if exchange_id == "bitmex":
        if market.get("inverse") is True:
            return 1.0
        multiplier = market.get("info", {}).get("underlyingToPositionMultiplier") or 0
        try:
            multiplier_value = float(multiplier)
        except (TypeError, ValueError):
            multiplier_value = 0.0
        if multiplier_value > 0 and price > 0:
            return price / multiplier_value
    return _market_cost_step(exchange, symbol, price)


def _align_base_amount(
    exchange, spot_symbol: str, perp_symbol: str, base_amount: float, spot_price: float, perp_price: float
) -> float:
    spot_step = _market_cost_step(exchange, spot_symbol, spot_price)
    perp_step = _perp_notional_step(exchange, perp_symbol, perp_price)
    step = max(spot_step, perp_step)
    if step <= 0 or spot_price <= 0:
        return base_amount
    notional = base_amount * spot_price
    aligned_notional = math.floor(notional / step) * step
    if aligned_notional <= 0:
        return base_amount
    return aligned_notional / spot_price


def _align_base_to_perp_precision(
    exchange, perp_symbol: str, base_amount: float, perp_price: float
) -> float:
    if _exchange_id(exchange) != "bitmex":
        return base_amount
    market = exchange.markets.get(perp_symbol) or {}
    inverse = market.get("inverse") is True
    if inverse:
        if perp_price <= 0:
            return base_amount
        amount_contracts = base_amount * perp_price
    else:
        multiplier = market.get("info", {}).get("underlyingToPositionMultiplier") or 1
        try:
            multiplier_value = float(multiplier)
        except (TypeError, ValueError):
            multiplier_value = 1.0
        if multiplier_value <= 0:
            return base_amount
        amount_contracts = base_amount * multiplier_value
    precise = exchange.amount_to_precision(perp_symbol, amount_contracts)
    try:
        precise_value = float(precise)
    except (TypeError, ValueError):
        return base_amount
    if inverse:
        return precise_value / perp_price
    return precise_value / multiplier_value


def spot_amount_to_precision(exchange, symbol: str, amount: float) -> float:
    exchange_id = _exchange_id(exchange)
    if exchange_id != "bitmex":
        return amount_to_precision(exchange, symbol, amount)
    market = exchange.markets.get(symbol) or {}
    multiplier = market.get("info", {}).get("underlyingToPositionMultiplier") or 1
    precise_units = exchange.amount_to_precision(symbol, amount)
    amount_units = float(precise_units)
    try:
        multiplier_value = float(multiplier)
    except (TypeError, ValueError):
        multiplier_value = 1.0
    if multiplier_value > 1:
        return amount_units / multiplier_value
    return amount_units


def to_perp_amount(config: dict, base_amount: float, price: float) -> float:
    if config.get("perp_size_mode") == "contracts":
        contract_size = config.get("perp_contract_size") or 0
        if contract_size <= 0:
            raise ValueError("Contract size non disponibile per il perp.")
        return base_amount / contract_size
    return base_amount


def perp_amount_to_precision(exchange, symbol: str, config: dict, base_amount: float, price: float) -> float:
    exchange_id = _exchange_id(exchange)
    if exchange_id == "bitmex":
        market = exchange.markets.get(symbol) or {}
        inverse = market.get("inverse") is True
        if inverse:
            amount = base_amount * price
        else:
            multiplier = market.get("info", {}).get("underlyingToPositionMultiplier") or 1
            try:
                multiplier_value = float(multiplier)
            except (TypeError, ValueError):
                multiplier_value = 1.0
            amount = base_amount * multiplier_value
        precise = exchange.amount_to_precision(symbol, amount)
        return float(precise)
    amount = to_perp_amount(config, base_amount, price)
    return amount_to_precision(exchange, symbol, amount)


def _log_sizes(exchange_id: str, spot_symbol: str, spot_amount: float, perp_symbol: str, perp_amount: float) -> None:
    if exchange_id == "bitmex":
        logger.debug(
            "bitmex order sizes spot=%s %.8f perp=%s %.8f",
            spot_symbol,
            spot_amount,
            perp_symbol,
            perp_amount,
        )


def weighted_avg(prev_avg: float, prev_qty: float, new_avg: float, new_qty: float) -> float:
    total_qty = prev_qty + new_qty
    if total_qty <= 0:
        return prev_avg
    if prev_avg is None:
        return new_avg
    return (prev_avg * prev_qty + new_avg * new_qty) / total_qty


async def start(
    db,
    exchange,
    user_id: int,
    exchange_account_id: int,
    asset: str,
    capital_usdc: float,
    strategy_key: str,
) -> Strategy:
    config = await ensure_strategy_config(exchange, asset, None)
    spot_symbol = config.get("spot_symbol")
    perp_symbol = config.get("perp_symbol")
    spot_price = await get_last_price(exchange, spot_symbol)
    perp_price = await get_last_price(exchange, perp_symbol)
    trade_capital = capital_usdc / FEE_BUFFER
    base_amount = trade_capital / spot_price
    base_amount = _align_base_amount(exchange, spot_symbol, perp_symbol, base_amount, spot_price, perp_price)
    base_amount = _align_base_to_perp_precision(exchange, perp_symbol, base_amount, perp_price)
    spot_amount = spot_amount_to_precision(exchange, spot_symbol, base_amount)
    perp_amount = perp_amount_to_precision(exchange, perp_symbol, config, base_amount, perp_price)
    _log_sizes(config.get("exchange"), spot_symbol, spot_amount, perp_symbol, perp_amount)
    if spot_amount <= 0 or perp_amount <= 0:
        raise ValueError("Invalid amount (too small)")
    spot_order = await exchange.create_market_buy_order(spot_symbol, spot_amount)
    filled = float(spot_order.get("filled") or spot_order.get("amount") or spot_amount)
    entry_spot_px = float(spot_order.get("average") or spot_price)
    try:
        perp_price = await get_last_price(exchange, perp_symbol)
        perp_amount = perp_amount_to_precision(exchange, perp_symbol, config, filled, perp_price)
        perp_order = await exchange.create_market_sell_order(perp_symbol, perp_amount)
    except Exception:
        await exchange.create_market_sell_order(spot_symbol, filled)
        raise
    entry_perp_px = float(perp_order.get("average") or perp_price)
    strategy = Strategy(
        user_id=user_id,
        exchange_account_id=exchange_account_id,
        asset=asset,
        strategy_key=strategy_key,
        name=STRATEGY_NAME,
        status=StrategyStatus.ACTIVE,
        allocated_capital_usdc=capital_usdc,
        total_quantity=filled,
        entry_spot_px=entry_spot_px,
        entry_perp_px=entry_perp_px,
        config=config,
    )
    db.add(strategy)
    await db.flush()
    position = StrategyPosition(
        strategy_id=strategy.id,
        allocated_capital_usdc=capital_usdc,
        quantity=filled,
        entry_spot_px=entry_spot_px,
        entry_perp_px=entry_perp_px,
    )
    db.add(position)
    return strategy


async def add(db, exchange, strategy: Strategy, added_amount_usdc: float) -> Strategy:
    asset = strategy.asset
    config = await ensure_strategy_config(exchange, asset, strategy.config or {})
    strategy.config = config
    spot_symbol = config.get("spot_symbol")
    perp_symbol = config.get("perp_symbol")
    spot_price = await get_last_price(exchange, spot_symbol)
    perp_price = await get_last_price(exchange, perp_symbol)
    trade_capital = added_amount_usdc / FEE_BUFFER
    base_amount = trade_capital / spot_price
    base_amount = _align_base_amount(exchange, spot_symbol, perp_symbol, base_amount, spot_price, perp_price)
    base_amount = _align_base_to_perp_precision(exchange, perp_symbol, base_amount, perp_price)
    spot_amount = spot_amount_to_precision(exchange, spot_symbol, base_amount)
    perp_amount = perp_amount_to_precision(exchange, perp_symbol, config, base_amount, perp_price)
    _log_sizes(config.get("exchange"), spot_symbol, spot_amount, perp_symbol, perp_amount)
    if spot_amount <= 0 or perp_amount <= 0:
        raise ValueError("Invalid amount (too small)")
    spot_order = await exchange.create_market_buy_order(spot_symbol, spot_amount)
    filled = float(spot_order.get("filled") or spot_order.get("amount") or spot_amount)
    entry_spot_px = float(spot_order.get("average") or spot_price)
    try:
        perp_price = await get_last_price(exchange, perp_symbol)
        perp_amount = perp_amount_to_precision(exchange, perp_symbol, config, filled, perp_price)
        perp_order = await exchange.create_market_sell_order(perp_symbol, perp_amount)
    except Exception:
        await exchange.create_market_sell_order(spot_symbol, filled)
        raise
    entry_perp_px = float(perp_order.get("average") or perp_price)
    prev_qty = strategy.total_quantity or 0.0
    strategy.total_quantity = prev_qty + filled
    strategy.allocated_capital_usdc += added_amount_usdc
    strategy.entry_spot_px = weighted_avg(strategy.entry_spot_px, prev_qty, entry_spot_px, filled)
    strategy.entry_perp_px = weighted_avg(strategy.entry_perp_px, prev_qty, entry_perp_px, filled)
    position = StrategyPosition(
        strategy_id=strategy.id,
        allocated_capital_usdc=added_amount_usdc,
        quantity=filled,
        entry_spot_px=entry_spot_px,
        entry_perp_px=entry_perp_px,
    )
    db.add(position)
    return strategy


async def remove(db, exchange, strategy: Strategy, remove_amount_usdc: float) -> float:
    asset = strategy.asset
    config = await ensure_strategy_config(exchange, asset, strategy.config or {})
    strategy.config = config
    spot_symbol = config.get("spot_symbol")
    perp_symbol = config.get("perp_symbol")
    spot_price = await get_last_price(exchange, spot_symbol)
    perp_price = await get_last_price(exchange, perp_symbol)
    base_qty = remove_amount_usdc / spot_price
    base_qty = _align_base_to_perp_precision(exchange, perp_symbol, base_qty, perp_price)
    spot_qty = spot_amount_to_precision(exchange, spot_symbol, base_qty)
    perp_qty = perp_amount_to_precision(exchange, perp_symbol, config, base_qty, perp_price)
    _log_sizes(config.get("exchange"), spot_symbol, spot_qty, perp_symbol, perp_qty)
    if spot_qty <= 0 or perp_qty <= 0:
        return 0.0
    if strategy.total_quantity and spot_qty > strategy.total_quantity:
        spot_qty = strategy.total_quantity
    perp_qty = perp_amount_to_precision(exchange, perp_symbol, config, spot_qty, perp_price)
    await exchange.create_market_buy_order(perp_symbol, perp_qty)
    await exchange.create_market_sell_order(spot_symbol, spot_qty)
    strategy.total_quantity = max(0.0, (strategy.total_quantity or 0.0) - spot_qty)
    strategy.allocated_capital_usdc = max(0.0, strategy.allocated_capital_usdc - remove_amount_usdc)
    if strategy.total_quantity <= 0:
        strategy.status = StrategyStatus.CLOSED
    return spot_qty


async def stop(db, exchange, strategy: Strategy) -> float:
    asset = strategy.asset
    config = await ensure_strategy_config(exchange, asset, strategy.config or {})
    strategy.config = config
    spot_symbol = config.get("spot_symbol")
    perp_symbol = config.get("perp_symbol")
    qty = strategy.total_quantity or 0.0
    perp_price = await get_last_price(exchange, perp_symbol)
    spot_qty = spot_amount_to_precision(exchange, spot_symbol, qty)
    perp_qty = perp_amount_to_precision(exchange, perp_symbol, config, qty, perp_price)
    _log_sizes(config.get("exchange"), spot_symbol, spot_qty, perp_symbol, perp_qty)
    if spot_qty <= 0 or perp_qty <= 0:
        strategy.status = StrategyStatus.CLOSED
        strategy.allocated_capital_usdc = 0.0
        strategy.total_quantity = 0.0
        return 0.0
    logger.info(
        "stop_strategy asset=%s spot=%s perp=%s spot_qty=%.8f perp_qty=%.8f perp_price=%.8f",
        asset,
        spot_symbol,
        perp_symbol,
        spot_qty,
        perp_qty,
        perp_price,
    )
    try:
        perp_order = await exchange.create_market_buy_order(perp_symbol, perp_qty)
        spot_order = await exchange.create_market_sell_order(spot_symbol, spot_qty)
    except Exception:
        logger.exception(
            "stop_strategy_failed asset=%s spot=%s perp=%s spot_qty=%.8f perp_qty=%.8f",
            asset,
            spot_symbol,
            perp_symbol,
            spot_qty,
            perp_qty,
        )
        raise
    exit_perp_px = float(perp_order.get("average") or perp_price)
    exit_spot_px = float(spot_order.get("average") or await get_last_price(exchange, spot_symbol))
    entry_spot_px = strategy.entry_spot_px or exit_spot_px
    entry_perp_px = strategy.entry_perp_px or exit_perp_px
    strategy.realized_pnl_usdc = (exit_spot_px - entry_spot_px) * spot_qty + (entry_perp_px - exit_perp_px) * spot_qty
    strategy.status = StrategyStatus.CLOSED
    strategy.allocated_capital_usdc = 0.0
    strategy.total_quantity = 0.0
    return spot_qty


class CashFundingStrategy(StrategyAdapter):
    key = STRATEGY_KEY
    name = STRATEGY_NAME

    def get_allowed_assets(self, exchange_id: str) -> List[str]:
        rules = get_exchange_rules(exchange_id)
        return rules.get("assets") or []

    def get_min_capital(self) -> float:
        return float(MIN_CAPITAL_USD)

    async def fetch_usdc_balance(self, exchange, adapter) -> float:
        return await fetch_usdc_balance(exchange, adapter)

    async def start(
        self,
        db: AsyncSession,
        exchange,
        user_id: int,
        exchange_account_id: int,
        asset: str,
        capital_usdc: float,
    ) -> Strategy:
        return await start(db, exchange, user_id, exchange_account_id, asset, capital_usdc, self.key)

    async def add(self, db: AsyncSession, exchange, strategy: Strategy, added_amount_usdc: float) -> Strategy:
        return await add(db, exchange, strategy, added_amount_usdc)

    async def remove(self, db: AsyncSession, exchange, strategy: Strategy, remove_amount_usdc: float) -> float:
        return await remove(db, exchange, strategy, remove_amount_usdc)

    async def stop(self, db: AsyncSession, exchange, strategy: Strategy) -> float:
        return await stop(db, exchange, strategy)
