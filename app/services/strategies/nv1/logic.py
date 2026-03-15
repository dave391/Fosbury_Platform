import logging
import math
from types import SimpleNamespace
from typing import Any, Optional

from app.services.strategies.nv1.rules import (
    STRATEGY_NAME,
    FEE_BUFFER,
    MIN_CAPITAL_USD,
    DEFAULT_LEVERAGE,
    MARGIN_SAFETY_BUFFER,
    MIN_ALLOCATION_PCT,
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


def to_perp_amount(config: dict, base_amount: float, _price: float) -> float:
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


async def stop(db, exchange, adapter, strategy) -> float:
    from core.enums import StrategyStatus

    asset = strategy.asset
    config = await ensure_strategy_config(exchange, asset, strategy.config or {})
    strategy.config = config
    spot_symbol = config.get("spot_symbol")
    perp_symbol = config.get("perp_symbol")
    position_info = await adapter.fetch_position_info(exchange, perp_symbol)
    live_size = abs(float((position_info or {}).get("size") or 0.0))
    qty = float(live_size or strategy.total_quantity or 0.0)
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
        "nv1_stop asset=%s spot=%s perp=%s spot_qty=%.8f perp_qty=%.8f perp_price=%.8f",
        asset,
        spot_symbol,
        perp_symbol,
        spot_qty,
        perp_qty,
        perp_price,
    )
    try:
        perp_order = await exchange.create_market_buy_order(perp_symbol, perp_qty)
    except Exception:
        logger.exception(
            "nv1_stop_short_close_failed asset=%s spot=%s perp=%s spot_qty=%.8f perp_qty=%.8f",
            asset,
            spot_symbol,
            perp_symbol,
            spot_qty,
            perp_qty,
        )
        raise
    remaining_position = await adapter.fetch_position_info(exchange, perp_symbol)
    remaining_size = abs(float((remaining_position or {}).get("size") or 0.0))
    if remaining_size > 0:
        remaining_mark = float((remaining_position or {}).get("mark_price") or perp_price)
        remaining_qty = perp_amount_to_precision(exchange, perp_symbol, config, remaining_size, remaining_mark)
        if remaining_qty > 0:
            await exchange.create_market_buy_order(perp_symbol, remaining_qty)
    spot_order = await exchange.create_market_sell_order(spot_symbol, spot_qty)
    exit_perp_px = float(perp_order.get("average") or perp_price)
    exit_spot_px = float(spot_order.get("average") or await get_last_price(exchange, spot_symbol))
    entry_spot_px = float(strategy.entry_spot_px or exit_spot_px)
    entry_perp_px = float(strategy.entry_perp_px or exit_perp_px)
    realized_pnl = (exit_spot_px - entry_spot_px) * spot_qty + (entry_perp_px - exit_perp_px) * spot_qty
    strategy.realized_pnl_usdc = float(realized_pnl)
    strategy.status = StrategyStatus.CLOSED
    strategy.allocated_capital_usdc = 0.0
    strategy.total_quantity = 0.0
    strategy.config = {
        **config,
        "last_exit_perp_px": float(exit_perp_px),
        "last_exit_spot_px": float(exit_spot_px),
        "last_closed_qty": float(spot_qty),
    }
    return float(spot_qty)


async def add(db, exchange, adapter, strategy, added_amount_usdc: float):
    asset = strategy.asset
    config = await ensure_strategy_config(exchange, asset, strategy.config or {})
    strategy.config = config
    spot_symbol = config.get("spot_symbol")
    perp_symbol = config.get("perp_symbol")
    spot_price = await get_last_price(exchange, spot_symbol)
    perp_price = await get_last_price(exchange, perp_symbol)
    leverage = float(DEFAULT_LEVERAGE)
    safety_buffer = float(MARGIN_SAFETY_BUFFER)
    trade_capital = float(added_amount_usdc) / float(FEE_BUFFER)
    base_amount = trade_capital / (spot_price * (1.0 + (safety_buffer / leverage)))
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
    real_spot_capital = float(spot_order.get("cost") or (entry_spot_px * filled))
    try:
        perp_price = await get_last_price(exchange, perp_symbol)
        perp_amount = perp_amount_to_precision(exchange, perp_symbol, config, filled, perp_price)
        perp_order = await exchange.create_market_sell_order(perp_symbol, perp_amount)
    except Exception:
        await exchange.create_market_sell_order(spot_symbol, filled)
        raise
    entry_perp_px = float(perp_order.get("average") or perp_price)
    prev_qty = float(strategy.total_quantity or 0.0)
    total_qty = float(prev_qty + filled)
    position_info = await adapter.fetch_position_info(exchange, perp_symbol)
    margin_already_allocated = float((position_info or {}).get("margin") or 0.0)
    total_target_margin = (float(total_qty) * float(spot_price) / leverage) * safety_buffer
    margin_to_add = max(float(total_target_margin) - float(margin_already_allocated), 0.0)
    if margin_to_add > 0:
        margin_result = await adapter.add_margin(exchange, perp_symbol, margin_to_add)
        if isinstance(margin_result, dict) and not margin_result.get("success", False):
            try:
                perp_filled = float(perp_order.get("filled") or perp_order.get("amount") or perp_amount)
                if perp_filled > 0:
                    await exchange.create_market_buy_order(perp_symbol, perp_filled)
            finally:
                await exchange.create_market_sell_order(spot_symbol, filled)
            raise ValueError(margin_result.get("error") or "add_margin failed")
    final_position_info = await adapter.fetch_position_info(exchange, perp_symbol)
    final_margin = float((final_position_info or {}).get("margin") or 0.0)
    if final_margin <= 0:
        final_margin = float(margin_already_allocated + margin_to_add)
    strategy.total_quantity = float(total_qty)
    strategy.allocated_capital_usdc = float(strategy.allocated_capital_usdc or 0.0) + float(real_spot_capital) + float(margin_to_add)
    strategy.entry_spot_px = weighted_avg(strategy.entry_spot_px, prev_qty, entry_spot_px, filled)
    strategy.entry_perp_px = weighted_avg(strategy.entry_perp_px, prev_qty, entry_perp_px, filled)
    notional = abs(float(strategy.total_quantity) * float(strategy.entry_perp_px or entry_perp_px))
    effective_leverage = None if final_margin <= 0 else float(notional / final_margin)
    strategy.config = {
        **config,
        "collateral_usdc": float(final_margin),
        "target_leverage": leverage,
        "margin_safety_buffer": safety_buffer,
        "target_margin": float(total_target_margin),
        "margin_already_allocated": float(margin_already_allocated),
        "margin_added": float(margin_to_add),
        "final_margin": float(final_margin),
        "effective_leverage": effective_leverage,
    }
    if db is not None:
        from core.models import StrategyPosition

        db.add(
            StrategyPosition(
                strategy_id=strategy.id,
                allocated_capital_usdc=float(real_spot_capital + margin_to_add),
                quantity=float(filled),
                entry_spot_px=entry_spot_px,
                entry_perp_px=entry_perp_px,
            )
        )
    return strategy


async def remove(db, exchange, adapter, strategy, remove_amount_usdc: float) -> float:
    from core.enums import StrategyStatus

    asset = strategy.asset
    config = await ensure_strategy_config(exchange, asset, strategy.config or {})
    strategy.config = config
    spot_symbol = config.get("spot_symbol")
    perp_symbol = config.get("perp_symbol")
    spot_price = await get_last_price(exchange, spot_symbol)
    perp_price = await get_last_price(exchange, perp_symbol)
    base_qty = float(remove_amount_usdc) / float(spot_price)
    base_qty = _align_base_to_perp_precision(exchange, perp_symbol, base_qty, perp_price)
    spot_qty = spot_amount_to_precision(exchange, spot_symbol, base_qty)
    if strategy.total_quantity and spot_qty > float(strategy.total_quantity):
        spot_qty = float(strategy.total_quantity)
    perp_qty = perp_amount_to_precision(exchange, perp_symbol, config, spot_qty, perp_price)
    _log_sizes(config.get("exchange"), spot_symbol, spot_qty, perp_symbol, perp_qty)
    if spot_qty <= 0 or perp_qty <= 0:
        return 0.0
    await exchange.create_market_buy_order(perp_symbol, perp_qty)
    spot_order = await exchange.create_market_sell_order(spot_symbol, spot_qty)
    removed_cost = spot_order.get("cost")
    removed_capital = float(removed_cost) if removed_cost is not None else float((strategy.entry_spot_px or spot_price) * spot_qty)
    strategy.total_quantity = max(0.0, float(strategy.total_quantity or 0.0) - float(spot_qty))
    strategy.allocated_capital_usdc = max(0.0, float(strategy.allocated_capital_usdc or 0.0) - float(removed_capital))
    final_position_info = await adapter.fetch_position_info(exchange, perp_symbol)
    final_margin = float((final_position_info or {}).get("margin") or 0.0)
    if strategy.total_quantity <= 0:
        strategy.status = StrategyStatus.CLOSED
        strategy.allocated_capital_usdc = 0.0
        final_margin = 0.0
    strategy.config = {
        **config,
        "collateral_usdc": float(final_margin),
        "final_margin": float(final_margin),
    }
    return float(spot_qty)


async def scale_up(db, exchange, adapter, strategy, excess_margin: float):
    asset = strategy.asset
    config = await ensure_strategy_config(exchange, asset, strategy.config or {})
    strategy.config = config
    spot_symbol = config.get("spot_symbol")
    perp_symbol = config.get("perp_symbol")
    margin_to_use = max(float(excess_margin or 0.0), 0.0)
    if margin_to_use <= 0:
        return {"executed": False, "reason": "no excess margin", "strategy": strategy}
    position_info = await adapter.fetch_position_info(exchange, perp_symbol)
    current_margin = float((position_info or {}).get("margin") or 0.0)
    initial_margin = float((position_info or {}).get("initial_margin") or 0.0)
    unrealized_pnl = abs(float((position_info or {}).get("unrealized_pnl") or 0.0))
    max_removable = max(float((current_margin - initial_margin - unrealized_pnl) * 0.995), 0.0)
    if max_removable <= 0:
        return {"executed": False, "reason": "no removable margin available", "strategy": strategy}
    removable = min(float(margin_to_use), float(max_removable))
    remove_result = await adapter.remove_margin(exchange, perp_symbol, removable)
    if isinstance(remove_result, dict) and not remove_result.get("success", False):
        raise ValueError(remove_result.get("error") or "remove_margin failed")
    spot_price = await get_last_price(exchange, spot_symbol)
    perp_price = await get_last_price(exchange, perp_symbol)
    leverage = float(DEFAULT_LEVERAGE)
    safety_buffer = float(MARGIN_SAFETY_BUFFER)
    base_amount = removable / (spot_price * (1.0 + (safety_buffer / leverage)))
    base_amount = _align_base_amount(exchange, spot_symbol, perp_symbol, base_amount, spot_price, perp_price)
    base_amount = _align_base_to_perp_precision(exchange, perp_symbol, base_amount, perp_price)
    spot_amount = spot_amount_to_precision(exchange, spot_symbol, base_amount)
    perp_amount = perp_amount_to_precision(exchange, perp_symbol, config, base_amount, perp_price)
    _log_sizes(config.get("exchange"), spot_symbol, spot_amount, perp_symbol, perp_amount)
    if spot_amount <= 0 or perp_amount <= 0:
        await adapter.add_margin(exchange, perp_symbol, removable)
        return {"executed": False, "reason": "additional size below minimum", "strategy": strategy}
    spot_order = await exchange.create_market_buy_order(spot_symbol, spot_amount)
    filled = float(spot_order.get("filled") or spot_order.get("amount") or spot_amount)
    entry_spot_px = float(spot_order.get("average") or spot_price)
    try:
        perp_price = await get_last_price(exchange, perp_symbol)
        perp_amount = perp_amount_to_precision(exchange, perp_symbol, config, filled, perp_price)
        perp_order = await exchange.create_market_sell_order(perp_symbol, perp_amount)
    except Exception as exc:
        rollback_errors = []
        try:
            await exchange.create_market_sell_order(spot_symbol, filled)
        except Exception as rollback_exc:
            rollback_errors.append(f"spot_rollback_failed: {rollback_exc}")
        try:
            await adapter.add_margin(exchange, perp_symbol, removable)
        except Exception as rollback_exc:
            rollback_errors.append(f"margin_rollback_failed: {rollback_exc}")
        if rollback_errors:
            raise RuntimeError(
                f"partial execution risk: short_open_failed={exc} | {' | '.join(rollback_errors)}"
            )
        raise
    entry_perp_px = float(perp_order.get("average") or perp_price)
    prev_qty = float(strategy.total_quantity or 0.0)
    total_qty = float(prev_qty + filled)
    position_info = await adapter.fetch_position_info(exchange, perp_symbol)
    margin_already_allocated = float((position_info or {}).get("margin") or 0.0)
    total_target_margin = (float(total_qty) * float(spot_price) / leverage) * safety_buffer
    margin_to_add = max(float(total_target_margin) - float(margin_already_allocated), 0.0)
    if margin_to_add > 0:
        margin_result = await adapter.add_margin(exchange, perp_symbol, margin_to_add)
        if isinstance(margin_result, dict) and not margin_result.get("success", False):
            rollback_errors = []
            perp_filled = float(perp_order.get("filled") or perp_order.get("amount") or perp_amount)
            if perp_filled > 0:
                try:
                    await exchange.create_market_buy_order(perp_symbol, perp_filled)
                except Exception as rollback_exc:
                    rollback_errors.append(f"perp_rollback_failed: {rollback_exc}")
            try:
                await exchange.create_market_sell_order(spot_symbol, filled)
            except Exception as rollback_exc:
                rollback_errors.append(f"spot_rollback_failed: {rollback_exc}")
            try:
                await adapter.add_margin(exchange, perp_symbol, removable)
            except Exception as rollback_exc:
                rollback_errors.append(f"margin_rollback_failed: {rollback_exc}")
            if rollback_errors:
                raise RuntimeError(
                    f"partial execution risk: post_order_margin_add_failed={margin_result.get('error') or 'add_margin failed'} | {' | '.join(rollback_errors)}"
                )
            raise ValueError(margin_result.get("error") or "add_margin failed")
    final_position_info = await adapter.fetch_position_info(exchange, perp_symbol)
    final_margin = float((final_position_info or {}).get("margin") or 0.0)
    if final_margin <= 0:
        final_margin = float(margin_already_allocated + margin_to_add)
    strategy.total_quantity = float(total_qty)
    strategy.entry_spot_px = weighted_avg(strategy.entry_spot_px, prev_qty, entry_spot_px, filled)
    strategy.entry_perp_px = weighted_avg(strategy.entry_perp_px, prev_qty, entry_perp_px, filled)
    notional = abs(float(strategy.total_quantity) * float(strategy.entry_perp_px or entry_perp_px))
    effective_leverage = None if final_margin <= 0 else float(notional / final_margin)
    strategy.config = {
        **config,
        "collateral_usdc": float(final_margin),
        "target_leverage": leverage,
        "margin_safety_buffer": safety_buffer,
        "target_margin": float(total_target_margin),
        "margin_already_allocated": float(margin_already_allocated),
        "margin_added": float(margin_to_add),
        "final_margin": float(final_margin),
        "effective_leverage": effective_leverage,
    }
    return {"executed": True, "strategy": strategy, "added_qty": float(filled)}


async def scale_down(db, exchange, adapter, strategy, mark_price: float):
    asset = strategy.asset
    config = await ensure_strategy_config(exchange, asset, strategy.config or {})
    strategy.config = config
    spot_symbol = config.get("spot_symbol")
    perp_symbol = config.get("perp_symbol")
    position_info = await adapter.fetch_position_info(exchange, perp_symbol)
    if not position_info:
        return {"executed": False, "reason": "no open position", "strategy": strategy}
    current_margin = float((position_info or {}).get("margin") or 0.0)
    live_mark = float(mark_price or 0.0)
    if live_mark <= 0:
        live_mark = float((position_info or {}).get("mark_price") or 0.0)
    if live_mark <= 0:
        live_mark = await get_last_price(exchange, perp_symbol)
    current_size = abs(float((position_info or {}).get("size") or strategy.total_quantity or 0.0))
    current_notional = float(current_size * live_mark)
    target_notional = float(current_margin * float(DEFAULT_LEVERAGE) / float(MARGIN_SAFETY_BUFFER))
    reduce_notional = float(current_notional - target_notional)
    reduce_base = 0.0 if live_mark <= 0 else float(reduce_notional / live_mark)
    if reduce_base <= 0:
        return {"executed": False, "reason": "no reduction required", "strategy": strategy}
    reduce_base = _align_base_to_perp_precision(exchange, perp_symbol, reduce_base, live_mark)
    reduce_base = min(float(reduce_base), float(strategy.total_quantity or 0.0))
    spot_qty = spot_amount_to_precision(exchange, spot_symbol, reduce_base)
    perp_qty = perp_amount_to_precision(exchange, perp_symbol, config, spot_qty, live_mark)
    _log_sizes(config.get("exchange"), spot_symbol, spot_qty, perp_symbol, perp_qty)
    if spot_qty <= 0 or perp_qty <= 0:
        return {"executed": False, "reason": "reduce amount below minimum", "strategy": strategy}
    total_qty = float(strategy.total_quantity or 0.0)
    if spot_qty >= total_qty > 0:
        await stop(db, exchange, adapter, strategy)
        return {"executed": True, "strategy": strategy, "reduced_qty": float(spot_qty)}
    await exchange.create_market_buy_order(perp_symbol, perp_qty)
    await exchange.create_market_sell_order(spot_symbol, spot_qty)
    strategy.total_quantity = max(0.0, float(total_qty - spot_qty))
    final_position_info = await adapter.fetch_position_info(exchange, perp_symbol)
    final_margin = float((final_position_info or {}).get("margin") or 0.0)
    notional = abs(float(strategy.total_quantity) * float(strategy.entry_perp_px or live_mark))
    effective_leverage = None if final_margin <= 0 else float(notional / final_margin)
    strategy.config = {
        **config,
        "collateral_usdc": float(final_margin),
        "final_margin": float(final_margin),
        "effective_leverage": effective_leverage,
    }
    return {"executed": True, "strategy": strategy, "reduced_qty": float(spot_qty)}


async def start(
    db,
    exchange,
    adapter,
    user_id: int,
    exchange_account_id: int,
    asset: str,
    capital_usdc: float,
    strategy_key: str,
    available_balance: Optional[float] = None,
) -> Any:
    if float(capital_usdc or 0.0) < float(MIN_CAPITAL_USD):
        raise ValueError(f"Minimum amount is {MIN_CAPITAL_USD} USDC.")
    exchange_id = _exchange_id(exchange)
    rules = _get_rules(exchange_id)
    if not rules.get("partial_allocation_allowed", True) and available_balance is not None:
        min_required = float(available_balance) * float(MIN_ALLOCATION_PCT)
        if float(capital_usdc) < min_required:
            raise ValueError(
                f"Allocated capital too low for {exchange_id}. "
                f"Required at least {MIN_ALLOCATION_PCT * 100:.0f}% of available balance."
            )

    config = await ensure_strategy_config(exchange, asset, None)
    spot_symbol = config.get("spot_symbol")
    perp_symbol = config.get("perp_symbol")
    if exchange_id == "bitmex":
        isolated_result = await adapter.ensure_isolated_margin(
            exchange, perp_symbol, float(DEFAULT_LEVERAGE)
        )
        if isinstance(isolated_result, dict) and not isolated_result.get("success", False):
            raise ValueError(isolated_result.get("error") or "cannot set isolated margin")
    spot_price = await get_last_price(exchange, spot_symbol)
    perp_price = await get_last_price(exchange, perp_symbol)
    trade_capital = float(capital_usdc) / float(FEE_BUFFER)
    leverage = float(DEFAULT_LEVERAGE)
    safety_buffer = float(MARGIN_SAFETY_BUFFER)
    base_amount = trade_capital / (spot_price * (1.0 + (safety_buffer / leverage)))
    base_amount = _align_base_amount(exchange, spot_symbol, perp_symbol, base_amount, spot_price, perp_price)
    base_amount = _align_base_to_perp_precision(exchange, perp_symbol, base_amount, perp_price)
    spot_amount = spot_amount_to_precision(exchange, spot_symbol, base_amount)
    perp_amount = perp_amount_to_precision(exchange, perp_symbol, config, base_amount, perp_price)
    _log_sizes(exchange_id, spot_symbol, spot_amount, perp_symbol, perp_amount)
    if spot_amount <= 0 or perp_amount <= 0:
        raise ValueError("Invalid amount (too small)")

    spot_order = await exchange.create_market_buy_order(spot_symbol, spot_amount)
    filled = float(spot_order.get("filled") or spot_order.get("amount") or spot_amount)
    entry_spot_px = float(spot_order.get("average") or spot_price)
    real_spot_capital = float(spot_order.get("cost") or (entry_spot_px * filled))

    try:
        perp_price = await get_last_price(exchange, perp_symbol)
        perp_amount = perp_amount_to_precision(exchange, perp_symbol, config, filled, perp_price)
        perp_order = await exchange.create_market_sell_order(perp_symbol, perp_amount)
    except Exception:
        await exchange.create_market_sell_order(spot_symbol, filled)
        raise

    entry_perp_px = float(perp_order.get("average") or perp_price)
    target_margin = (float(real_spot_capital) / leverage) * safety_buffer
    position_info = await adapter.fetch_position_info(exchange, perp_symbol)
    margin_already_allocated = float((position_info or {}).get("margin") or 0.0)
    margin_to_add = max(float(target_margin) - float(margin_already_allocated), 0.0)
    if margin_to_add > 0:
        margin_result = await adapter.add_margin(exchange, perp_symbol, margin_to_add)
        if isinstance(margin_result, dict) and not margin_result.get("success", False):
            try:
                perp_filled = float(perp_order.get("filled") or perp_order.get("amount") or perp_amount)
                if perp_filled > 0:
                    await exchange.create_market_buy_order(perp_symbol, perp_filled)
            finally:
                await exchange.create_market_sell_order(spot_symbol, filled)
            raise ValueError(margin_result.get("error") or "add_margin failed")
    final_position_info = await adapter.fetch_position_info(exchange, perp_symbol)
    final_margin = float((final_position_info or {}).get("margin") or 0.0)
    if final_margin <= 0:
        final_margin = float(margin_already_allocated + margin_to_add)
    notional = abs(float(filled) * float(entry_perp_px))
    effective_leverage = None if final_margin <= 0 else float(notional / final_margin)
    allocated_capital = float(real_spot_capital + final_margin)
    config = {
        **config,
        "collateral_usdc": float(final_margin),
        "target_leverage": leverage,
        "margin_safety_buffer": safety_buffer,
        "target_margin": float(target_margin),
        "margin_already_allocated": float(margin_already_allocated),
        "margin_added": float(margin_to_add),
        "final_margin": float(final_margin),
        "effective_leverage": effective_leverage,
    }

    if db is None:
        return SimpleNamespace(
            id=None,
            user_id=user_id,
            exchange_account_id=exchange_account_id,
            asset=asset,
            strategy_key=strategy_key,
            name=STRATEGY_NAME,
            status="ACTIVE",
            allocated_capital_usdc=allocated_capital,
            total_quantity=filled,
            entry_spot_px=entry_spot_px,
            entry_perp_px=entry_perp_px,
            config=config,
        )

    from core.enums import StrategyStatus
    from core.models import Strategy, StrategyPosition

    strategy = Strategy(
        user_id=user_id,
        exchange_account_id=exchange_account_id,
        asset=asset,
        strategy_key=strategy_key,
        name=STRATEGY_NAME,
        status=StrategyStatus.ACTIVE,
        allocated_capital_usdc=allocated_capital,
        total_quantity=filled,
        entry_spot_px=entry_spot_px,
        entry_perp_px=entry_perp_px,
        config=config,
    )
    position = StrategyPosition(
        strategy_id=strategy.id,
        allocated_capital_usdc=allocated_capital,
        quantity=filled,
        entry_spot_px=entry_spot_px,
        entry_perp_px=entry_perp_px,
    )
    if db is not None:
        db.add(strategy)
        await db.flush()
        position.strategy_id = strategy.id
        db.add(position)
    return strategy
