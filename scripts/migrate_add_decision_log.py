import asyncio

from sqlalchemy import text

from core.database import engine


async def migrate():
    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                create table if not exists public.decision_log (
                    id serial primary key,
                    strategy_id integer not null references public.strategies(id),
                    strategy_key varchar not null,
                    timestamp timestamptz not null,
                    last_seen timestamptz not null,
                    action varchar not null,
                    reason varchar null,
                    executed boolean null,
                    execution_error varchar null,
                    price_at_decision double precision null,
                    liquidation_distance_pct double precision null,
                    excess_margin double precision null,
                    metrics_snapshot json null,
                    created_at timestamptz not null default now()
                )
                """
            )
        )
        await conn.execute(
            text("create index if not exists idx_decision_log_strategy_id on public.decision_log(strategy_id)")
        )
    print("decision_log migration completed")


if __name__ == "__main__":
    asyncio.run(migrate())
