import asyncio
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import select

from core.database import AsyncSessionLocal
from core.enums import StrategyStatus
from core.models import EquitySnapshot, Strategy, ExchangeAccount
from app.services.exchange_service import ExchangeService


async def run_snapshot_batch(snapshot_date: Optional[date] = None):
    snapshot_day = snapshot_date or (date.today() - timedelta(days=1))
    start_dt = datetime.combine(snapshot_day, time.min, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)
    run_id = uuid4().hex

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Strategy).where(Strategy.status == StrategyStatus.ACTIVE)
        )
        strategies = result.scalars().all()
        if not strategies:
            return

        strategies_by_account = {}
        for strategy in strategies:
            if not strategy.exchange_account_id:
                continue
            strategies_by_account.setdefault(strategy.exchange_account_id, []).append(strategy)

        exchange_service = ExchangeService(db)
        for account_id, account_strategies in strategies_by_account.items():
            account_result = await db.execute(
                select(ExchangeAccount).where(ExchangeAccount.id == account_id)
            )
            account = account_result.scalars().first()
            if not account:
                continue
            exchange = await exchange_service.get_exchange_client_by_account(account_id)
            if not exchange:
                continue
            adapter = exchange_service.get_exchange_adapter(account.exchange_name)
            try:
                for strategy in account_strategies:
                    existing_result = await db.execute(
                        select(EquitySnapshot).where(
                            EquitySnapshot.strategy_id == strategy.id,
                            EquitySnapshot.snapshot_date == snapshot_day,
                        )
                    )
                    existing = existing_result.scalars().first()

                    funding_delta, fees_delta = await adapter.fetch_strategy_deltas(
                        exchange, strategy, start_ms, end_ms
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
                await db.commit()
            finally:
                await exchange.close()


if __name__ == "__main__":
    asyncio.run(run_snapshot_batch())
