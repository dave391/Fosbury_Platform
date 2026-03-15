import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import select, update

from app.services.exchange_service import ExchangeService
from app.services.strategies.common import get_last_price
from app.services.strategies.nv1.logic import ensure_strategy_config, scale_down, scale_up, stop
from app.services.strategies.nv1.position_manager import compute_metrics
from app.services.strategies.nv1.strategy_engine import DEFAULT_THRESHOLDS, decide
from core.database import AsyncSessionLocal
from core.enums import StrategyStatus
from core.models import DecisionLog, ExchangeAccount, Strategy


logger = logging.getLogger(__name__)
last_logged_state = {}


def _fmt_num(value, digits: int = 2) -> str:
    try:
        return "n/a" if value is None else f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "n/a"


def _build_thresholds(config: dict) -> dict:
    return {key: config.get(key, value) for key, value in DEFAULT_THRESHOLDS.items()}


async def _log_decision_state(
    db,
    strategy_id,
    strategy_key,
    action,
    reason,
    metrics,
    executed,
    execution_error=None,
):
    now = datetime.now(timezone.utc)
    current_state = (action, executed)
    previous = last_logged_state.get(strategy_id)
    previous_state = (previous.get("action"), previous.get("executed")) if previous else None
    if current_state != previous_state:
        log_entry = DecisionLog(
            strategy_id=strategy_id,
            strategy_key=strategy_key,
            timestamp=now,
            last_seen=now,
            action=action,
            reason=reason,
            executed=executed,
            execution_error=execution_error,
            price_at_decision=metrics.get("mark_price"),
            liquidation_distance_pct=metrics.get("liquidation_distance_pct"),
            excess_margin=metrics.get("excess_margin"),
            metrics_snapshot=metrics,
        )
        db.add(log_entry)
        await db.flush()
        last_logged_state[strategy_id] = {"action": action, "executed": executed, "log_id": log_entry.id}
        return
    if previous and previous.get("log_id"):
        await db.execute(
            update(DecisionLog)
            .where(DecisionLog.id == previous["log_id"])
            .values(last_seen=now)
        )


async def run_cycle():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Strategy).where(
                Strategy.strategy_key == "nv1",
                Strategy.status == StrategyStatus.ACTIVE,
            )
        )
        strategies = result.scalars().all()
        if not strategies:
            logger.info("No active NV1 strategies")
            return
        strategies_by_account = {}
        for strategy in strategies:
            if not strategy.exchange_account_id:
                logger.warning("Strategy #%s skipped: missing exchange_account_id", strategy.id)
                continue
            strategies_by_account.setdefault(strategy.exchange_account_id, []).append(strategy)
        account_ids = list(strategies_by_account.keys())
        account_result = await db.execute(select(ExchangeAccount).where(ExchangeAccount.id.in_(account_ids)))
        account_map = {account.id: account for account in account_result.scalars().all()}
        exchange_service = ExchangeService(db)
        exchange_clients = {}
        price_cache = {}
        try:
            for account_id, account_strategies in strategies_by_account.items():
                account = account_map.get(account_id)
                if not account:
                    logger.warning("Account #%s not found", account_id)
                    continue
                exchange = await exchange_service.get_exchange_client_by_account(account_id)
                if not exchange:
                    logger.warning("Exchange client not available for account #%s", account_id)
                    continue
                exchange_clients[account_id] = exchange
                adapter = exchange_service.get_exchange_adapter(account.exchange_name)
                for strategy in account_strategies:
                    strategy_id = strategy.id
                    strategy_key = strategy.strategy_key
                    strategy_asset = strategy.asset
                    try:
                        config = await ensure_strategy_config(exchange, strategy_asset, strategy.config or {})
                        perp_symbol = config.get("perp_symbol")
                        if not perp_symbol:
                            logger.warning("Strategy #%s skipped: missing perp_symbol", strategy_id)
                            continue
                        cache_key = f"{account.exchange_name}:{perp_symbol}"
                        if cache_key not in price_cache:
                            price_cache[cache_key] = await get_last_price(exchange, perp_symbol)
                        price = price_cache[cache_key]
                        position_info = await adapter.fetch_position_info(exchange, perp_symbol)
                        if not position_info:
                            logger.warning("Strategy #%s skipped: no open position on %s", strategy_id, perp_symbol)
                            continue
                        strategy_data = {
                            "total_quantity": strategy.total_quantity,
                            "target_leverage": (strategy.config or {}).get("target_leverage", 5.0),
                        }
                        metrics = compute_metrics(position_info, strategy_data)
                        strategy_config = strategy.config or {}
                        decision = decide(
                            metrics,
                            _build_thresholds(strategy_config),
                            last_action_timestamp=strategy_config.get("last_action_timestamp"),
                        )
                        action = decision.get("action")
                        reason = decision.get("reason")
                        logger.info(
                            "Strategy #%s (%s/%s) | Price: %s | Liq dist: %s%% | Excess margin: %s | Action: %s | Reason: %s",
                            strategy_id,
                            strategy_asset,
                            account.exchange_name.upper(),
                            _fmt_num(price),
                            _fmt_num(metrics.get("liquidation_distance_pct")),
                            _fmt_num(metrics.get("excess_margin")),
                            action,
                            reason,
                        )
                        if action == "HOLD":
                            try:
                                await _log_decision_state(db, strategy_id, strategy_key, action, reason, metrics, None)
                                await db.commit()
                            except Exception as exc:
                                await db.rollback()
                                logger.error("Strategy #%s: HOLD decision log failed: %s", strategy_id, exc)
                            continue
                        try:
                            result = {"executed": False, "reason": "unknown"}
                            if action == "SCALE_UP":
                                params = decision.get("params") or {}
                                result = await scale_up(db, exchange, adapter, strategy, float(params.get("excess_margin") or 0.0))
                            elif action == "SCALE_DOWN":
                                result = await scale_down(db, exchange, adapter, strategy, float(metrics.get("mark_price") or price))
                            elif action == "EMERGENCY_CLOSE":
                                await stop(db, exchange, adapter, strategy)
                                result = {"executed": True}
                            else:
                                logger.warning("Strategy #%s skipped: unsupported action %s", strategy_id, action)
                                continue
                            if result.get("executed"):
                                updated_config = dict(strategy.config or {})
                                updated_config["last_action_timestamp"] = time.time()
                                strategy.config = updated_config
                                await _log_decision_state(db, strategy_id, strategy_key, action, reason, metrics, True)
                                await db.commit()
                                new_info = await adapter.fetch_position_info(exchange, perp_symbol) or {}
                                logger.info(
                                    "Strategy #%s: executed %s successfully | New size: %s | New margin: %s",
                                    strategy_id,
                                    action,
                                    _fmt_num(new_info.get("size")),
                                    _fmt_num(new_info.get("margin")),
                                )
                            else:
                                await _log_decision_state(
                                    db,
                                    strategy_id,
                                    strategy_key,
                                    action,
                                    reason,
                                    metrics,
                                    False,
                                    result.get("reason", "skipped"),
                                )
                                await db.commit()
                                logger.info("Strategy #%s: %s skipped — %s", strategy_id, action, result.get("reason", "unknown"))
                        except Exception as exc:
                            await db.rollback()
                            logger.error("Strategy #%s: %s failed: %s", strategy_id, action, exc)
                            if "partial execution risk" in str(exc).lower():
                                logger.critical("Strategy #%s: potential partial execution, manual check required", strategy_id)
                            try:
                                await _log_decision_state(
                                    db,
                                    strategy_id,
                                    strategy_key,
                                    action,
                                    reason,
                                    metrics,
                                    False,
                                    str(exc),
                                )
                                await db.commit()
                            except Exception as log_exc:
                                await db.rollback()
                                logger.error("Strategy #%s: failed to write decision log after error: %s", strategy_id, log_exc)
                    except Exception as exc:
                        await db.rollback()
                        logger.error("Strategy #%s processing failed: %s", strategy_id, exc)
        finally:
            for exchange in exchange_clients.values():
                try:
                    await exchange.close()
                except Exception:
                    logger.exception("Error closing exchange client")


async def run_orchestrator():
    logger.info("Orchestrator starting...")
    while True:
        cycle_start = time.time()
        try:
            await run_cycle()
        except Exception as exc:
            logger.error("Orchestrator cycle error: %s", exc)
        elapsed = time.time() - cycle_start
        await asyncio.sleep(max(0.0, 5.0 - elapsed))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    try:
        asyncio.run(run_orchestrator())
    except KeyboardInterrupt:
        logger.info("Orchestrator stopped")
