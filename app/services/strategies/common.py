import logging
import math
from typing import Callable, Optional


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


def exchange_id(exchange) -> str:
    return getattr(exchange, "id", "") or ""


def pick_market(markets, base: str, quote: str, market_type: str):
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


def _market_from_symbol(exchange, symbol: str, market_type: str, quote: str):
    market = (exchange.markets or {}).get(symbol)
    if not isinstance(market, dict):
        return None
    if not market.get(market_type):
        return None
    if str(market.get("quote") or "").upper() != str(quote or "").upper():
        return None
    return market


async def build_strategy_config(
    exchange,
    asset: str,
    rules: dict,
    validate_asset: Optional[Callable[[dict, str], None]] = None,
) -> dict:
    rules = rules or {}
    if not exchange.markets:
        await exchange.load_markets()
    if validate_asset is not None:
        validate_asset(rules, asset)
    quote = rules.get("quote") or "USDC"
    aliases = rules.get("spot_asset_aliases") or {}
    spot_asset = aliases.get(asset, asset)
    spot_symbol_overrides = rules.get("spot_symbol_overrides") or {}
    perp_symbol_overrides = rules.get("perp_symbol_overrides") or {}
    markets = list(exchange.markets.values())
    spot_market = _market_from_symbol(exchange, spot_symbol_overrides.get(asset), "spot", quote)
    perp_market = _market_from_symbol(exchange, perp_symbol_overrides.get(asset), "swap", quote)
    if not spot_market:
        spot_market = pick_market(markets, spot_asset, quote, "spot")
    if not perp_market:
        perp_market = pick_market(markets, asset, quote, "swap")
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
        "exchange": exchange_id(exchange),
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


async def ensure_strategy_config(
    exchange,
    asset: str,
    config: dict,
    rules: dict,
    validate_asset: Optional[Callable[[dict, str], None]] = None,
) -> dict:
    rules = rules or {}
    if config and config.get("spot_symbol") and config.get("perp_symbol"):
        return config
    return await build_strategy_config(exchange, asset, rules, validate_asset)


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
    if exchange_id(exchange) == "bitmex":
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
    if exchange_id(exchange) == "bitmex":
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
    precise = exchange.amount_to_precision(perp_symbol, base_amount)
    try:
        return float(precise)
    except (TypeError, ValueError):
        return base_amount


def spot_amount_to_precision(exchange, symbol: str, amount: float) -> float:
    if exchange_id(exchange) != "bitmex":
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


def to_perp_amount(config: dict, base_amount: float, _price: float) -> float:
    if config.get("perp_size_mode") == "contracts":
        contract_size = config.get("perp_contract_size") or 0
        if contract_size <= 0:
            raise ValueError("Contract size non disponibile per il perp.")
        return base_amount / contract_size
    return base_amount


def perp_amount_to_precision(exchange, symbol: str, config: dict, base_amount: float, price: float) -> float:
    if exchange_id(exchange) == "bitmex":
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


def log_sizes(exchange: str, spot_symbol: str, spot_amount: float, perp_symbol: str, perp_amount: float) -> None:
    if exchange == "bitmex":
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
