import asyncio
import os
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.engine.url import make_url

from core.config import settings
from core.database import AsyncSessionLocal
from core.enums import StrategyStatus
from core.models import EquitySnapshot, Strategy, ExchangeAccount
from app.services.exchange_service import ExchangeService


async def run_snapshot_batch(snapshot_date: Optional[date] = None):
    snapshot_day = snapshot_date or (date.today() - timedelta(days=1))
    start_dt = datetime.combine(snapshot_day, time.min, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)
    end_ms = int(end_dt.timestamp() * 1000)
    run_id = uuid4().hex
    debug = os.getenv("CRON_DEBUG", "").strip().lower() in ("1", "true", "yes", "on")
    try:
        parsed_url = make_url(settings.DATABASE_URL)
        db_host = parsed_url.host
        db_name = parsed_url.database
        db_user = parsed_url.username
    except Exception:
        db_host = None
        db_name = None
        db_user = None

    print(
        f"[equity_snapshot] start run_id={run_id} snapshot_day={snapshot_day.isoformat()} "
        f"window_utc={start_dt.isoformat()}..{end_dt.isoformat()} db_host={db_host} db_name={db_name} db_user={db_user}"
    )

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Strategy).where(Strategy.status == StrategyStatus.ACTIVE)
        )
        strategies = result.scalars().all()
        if not strategies:
            print(f"[equity_snapshot] no active strategies, run_id={run_id}")
            return

        strategies_by_account = {}
        for strategy in strategies:
            if not strategy.exchange_account_id:
                continue
            strategies_by_account.setdefault(strategy.exchange_account_id, []).append(strategy)

        exchange_service = ExchangeService(db)
        total_strategies = len(strategies)
        total_accounts = len(strategies_by_account)
        created = 0
        updated = 0
        skipped_missing_account = 0
        skipped_missing_exchange = 0
        skipped_exception = 0

        if debug:
            print(
                f"[equity_snapshot] active_strategies={total_strategies} accounts_with_strategies={total_accounts} run_id={run_id}"
            )

        for account_id, account_strategies in strategies_by_account.items():
            account_result = await db.execute(
                select(ExchangeAccount).where(ExchangeAccount.id == account_id)
            )
            account = account_result.scalars().first()
            if not account:
                skipped_missing_account += len(account_strategies)
                if debug:
                    print(
                        f"[equity_snapshot] skip account_id={account_id} reason=account_not_found strategies={len(account_strategies)} run_id={run_id}"
                    )
                continue
            exchange = await exchange_service.get_exchange_client_by_account(account_id)
            if not exchange:
                skipped_missing_exchange += len(account_strategies)
                if debug:
                    print(
                        f"[equity_snapshot] skip account_id={account_id} reason=exchange_not_configured strategies={len(account_strategies)} exchange={account.exchange_name} run_id={run_id}"
                    )
                continue
            adapter = exchange_service.get_exchange_adapter(account.exchange_name)
            try:
                for strategy in account_strategies:
                    try:
                        existing_result = await db.execute(
                            select(EquitySnapshot).where(
                                EquitySnapshot.strategy_id == strategy.id,
                                EquitySnapshot.snapshot_date == snapshot_day,
                            )
                        )
                        existing = existing_result.scalars().first()

                        strategy_start = strategy.created_at
                        if strategy_start and strategy_start.tzinfo is None:
                            strategy_start = strategy_start.replace(tzinfo=timezone.utc)
                        effective_start_dt = start_dt
                        if strategy_start and strategy_start > effective_start_dt:
                            effective_start_dt = strategy_start
                        if effective_start_dt >= end_dt:
                            continue
                        effective_start_ms = int(effective_start_dt.timestamp() * 1000)
                        funding_delta, fees_delta = await adapter.fetch_strategy_deltas(
                            exchange, strategy, effective_start_ms, end_ms
                        )

                        last_result = await db.execute(
                            select(EquitySnapshot)
                            .where(
                                EquitySnapshot.strategy_id == strategy.id,
                                EquitySnapshot.snapshot_date < snapshot_day,
                            )
                            .order_by(EquitySnapshot.snapshot_date.desc())
                        )
                        last_snapshot = last_result.scalars().first()
                        base_equity = (
                            last_snapshot.equity_usdc
                            if last_snapshot
                            else strategy.allocated_capital_usdc
                        )
                        equity_usdc = base_equity + (funding_delta - fees_delta)

                        if existing:
                            existing.equity_usdc = equity_usdc
                            existing.funding_delta_usdc = funding_delta
                            existing.fees_delta_usdc = fees_delta
                            existing.run_id = run_id
                            existing.as_of = end_dt
                            updated += 1
                        else:
                            db.add(
                                EquitySnapshot(
                                    strategy_id=strategy.id,
                                    snapshot_date=snapshot_day,
                                    equity_usdc=equity_usdc,
                                    funding_delta_usdc=funding_delta,
                                    fees_delta_usdc=fees_delta,
                                    run_id=run_id,
                                    as_of=end_dt,
                                )
                            )
                            created += 1
                    except Exception as e:
                        skipped_exception += 1
                        if debug:
                            print(
                                f"[equity_snapshot] error account_id={account_id} strategy_id={strategy.id} "
                                f"exchange={account.exchange_name} err={type(e).__name__}:{e} run_id={run_id}"
                            )
                await db.commit()
            finally:
                await exchange.close()

        print(
            f"[equity_snapshot] done run_id={run_id} active_strategies={total_strategies} "
            f"accounts={total_accounts} created={created} updated={updated} "
            f"skipped_missing_account={skipped_missing_account} skipped_missing_exchange={skipped_missing_exchange} "
            f"skipped_exception={skipped_exception}"
        )


if __name__ == "__main__":
    asyncio.run(run_snapshot_batch())
