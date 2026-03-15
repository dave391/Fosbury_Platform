import asyncio

from sqlalchemy import text

from core.database import engine


async def migrate():
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "alter table public.exchange_accounts add column if not exists cached_balance_usdc double precision null"
            )
        )
        await conn.execute(
            text(
                "alter table public.exchange_accounts add column if not exists balance_updated_at timestamptz null"
            )
        )
    print("exchange_accounts balance cache migration completed")


if __name__ == "__main__":
    asyncio.run(migrate())
