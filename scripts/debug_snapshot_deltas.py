import argparse
import asyncio
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select

from app.services.exchange_service import ExchangeService
from core.database import AsyncSessionLocal
from core.enums import StrategyStatus
from core.models import ExchangeAccount, Strategy


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", dest="snapshot_date", default=None)
    parser.add_argument("--exchange", dest="exchange_name", default="hyperliquid")
    parser.add_argument("--strategy-key", dest="strategy_key", default=None)
    parser.add_argument("--strategy-id", dest="strategy_id", type=int, default=None)
    parser.add_argument("--include-closed", action="store_true")
    parser.add_argument("--show-logs", action="store_true")
    parser.add_argument("--show-raw-ledger", action="store_true")
    parser.add_argument("--show-alt-sources", action="store_true")
    parser.add_argument("--log-limit", type=int, default=10)
    parser.add_argument("--from-start", action="store_true")
    return parser.parse_args()


async def main():
    args = _parse_args()
    snapshot_day = (
        datetime.strptime(args.snapshot_date, "%Y-%m-%d").date()
        if args.snapshot_date
        else (date.today() - timedelta(days=1))
    )
    start_dt = datetime.combine(snapshot_day, time.min, tzinfo=timezone.utc)
    end_dt = datetime.now(timezone.utc) if args.from_start else (start_dt + timedelta(days=1))
    end_ms = int(end_dt.timestamp() * 1000)

    async with AsyncSessionLocal() as db:
        exchange_service = ExchangeService(db)
        query = (
            select(Strategy, ExchangeAccount)
            .join(ExchangeAccount, ExchangeAccount.id == Strategy.exchange_account_id)
            .where(ExchangeAccount.exchange_name == args.exchange_name)
            .order_by(Strategy.id.asc())
        )
        if not args.include_closed:
            query = query.where(Strategy.status == StrategyStatus.ACTIVE)
        if args.strategy_key:
            query = query.where(Strategy.strategy_key == args.strategy_key)
        if args.strategy_id:
            query = query.where(Strategy.id == args.strategy_id)

        rows = (await db.execute(query)).all()
        if not rows:
            print("Nessuna strategia trovata con i filtri richiesti.")
            return

        print(
            f"[debug_snapshot_deltas] date={snapshot_day.isoformat()} "
            f"window_utc={start_dt.isoformat()}..{end_dt.isoformat()} "
            f"exchange={args.exchange_name} total={len(rows)}"
        )

        rows_by_account = {}
        for strategy, account in rows:
            rows_by_account.setdefault(account.id, {"account": account, "strategies": []})
            rows_by_account[account.id]["strategies"].append(strategy)

        for account_id, bucket in rows_by_account.items():
            account = bucket["account"]
            strategies = bucket["strategies"]
            try:
                exchange = await exchange_service.get_exchange_client_by_account(account_id)
            except Exception as exc:
                print(
                    f"[account={account_id}] exchange={account.exchange_name} "
                    f"strategies={len(strategies)} error={type(exc).__name__}:{exc}"
                )
                continue
            if not exchange:
                print(
                    f"[account={account_id}] exchange={account.exchange_name} "
                    f"strategies={len(strategies)} error=exchange_not_configured"
                )
                continue
            adapter = exchange_service.get_exchange_adapter(account.exchange_name)
            try:
                print(
                    f"[account={account_id}] exchange={account.exchange_name} "
                    f"strategies={len(strategies)}"
                )
                for strategy in strategies:
                    strategy_start = strategy.created_at
                    if strategy_start and strategy_start.tzinfo is None:
                        strategy_start = strategy_start.replace(tzinfo=timezone.utc)
                    effective_start_dt = strategy_start if args.from_start else start_dt
                    if strategy_start and strategy_start > effective_start_dt:
                        effective_start_dt = strategy_start
                    if effective_start_dt >= end_dt:
                        print(
                            f"  - strategy_id={strategy.id} key={strategy.strategy_key} "
                            f"asset={strategy.asset} status={strategy.status} skipped=outside_window"
                        )
                        continue
                    effective_start_ms = int(effective_start_dt.timestamp() * 1000)
                    funding_delta, fees_delta = await adapter.fetch_strategy_deltas(
                        exchange, strategy, effective_start_ms, end_ms
                    )
                    print(
                        f"  - strategy_id={strategy.id} key={strategy.strategy_key} "
                        f"asset={strategy.asset} status={strategy.status} "
                        f"funding_delta={float(funding_delta):.8f} fees_delta={float(fees_delta):.8f}"
                    )
                    if args.show_logs:
                        config = strategy.config or {}
                        quote = str(config.get("quote") or "USDC")
                        logs = await adapter.fetch_transaction_logs(
                            exchange, quote, effective_start_ms, end_ms
                        )
                        print(
                            f"    logs_count={len(logs)} quote={quote} sample_limit={args.log_limit}"
                        )
                        for item in (logs or [])[: max(0, int(args.log_limit))]:
                            print(f"    {item}")
                    if args.show_raw_ledger:
                        config = strategy.config or {}
                        quote = str(config.get("quote") or "USDC")
                        try:
                            raw_ledger = await exchange.fetch_ledger(
                                quote,
                                effective_start_ms,
                                500,
                                {"until": end_ms},
                            )
                        except Exception as exc:
                            print(f"    raw_ledger_error={type(exc).__name__}:{exc}")
                            raw_ledger = []
                        print(
                            f"    raw_ledger_count={len(raw_ledger or [])} quote={quote} sample_limit={args.log_limit}"
                        )
                        for item in (raw_ledger or [])[: max(0, int(args.log_limit))]:
                            print(f"    {item}")
                    if args.show_alt_sources:
                        config = strategy.config or {}
                        perp_symbol = config.get("perp_symbol") or config.get("perp_id")
                        spot_symbol = config.get("spot_symbol") or config.get("spot_id")
                        try:
                            funding_history = await exchange.fetch_funding_history(
                                perp_symbol,
                                effective_start_ms,
                                500,
                                {"until": end_ms},
                            )
                        except Exception as exc:
                            print(f"    funding_history_error={type(exc).__name__}:{exc}")
                            funding_history = []
                        print(
                            f"    funding_history_count={len(funding_history or [])} perp_symbol={perp_symbol} sample_limit={args.log_limit}"
                        )
                        for item in (funding_history or [])[: max(0, int(args.log_limit))]:
                            print(f"    {item}")
                        for trade_symbol in [perp_symbol, spot_symbol]:
                            if not trade_symbol:
                                continue
                            try:
                                my_trades = await exchange.fetch_my_trades(
                                    trade_symbol,
                                    effective_start_ms,
                                    500,
                                    {"until": end_ms},
                                )
                            except Exception as exc:
                                print(
                                    f"    my_trades_error symbol={trade_symbol} error={type(exc).__name__}:{exc}"
                                )
                                my_trades = []
                            print(
                                f"    my_trades_count={len(my_trades or [])} symbol={trade_symbol} sample_limit={args.log_limit}"
                            )
                            for item in (my_trades or [])[: max(0, int(args.log_limit))]:
                                print(f"    {item}")
            except Exception as exc:
                print(
                    f"[account={account_id}] exchange={account.exchange_name} "
                    f"error={type(exc).__name__}:{exc}"
                )
            finally:
                await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
