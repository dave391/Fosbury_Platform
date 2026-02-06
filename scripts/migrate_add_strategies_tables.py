import asyncio

from sqlalchemy import text

from core.database import engine


async def migrate():
    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                create table if not exists public.exchange_accounts (
                    id serial primary key,
                    user_id integer not null references public.users(id),
                    exchange_name varchar not null default 'deribit',
                    label varchar null,
                    created_at timestamptz not null default now(),
                    disabled_at timestamptz null
                )
                """
            )
        )
        await conn.execute(
            text("create index if not exists idx_exchange_accounts_user_id on public.exchange_accounts(user_id)")
        )
        await conn.execute(
            text(
                """
                create table if not exists public.strategies (
                    id serial primary key,
                    user_id integer not null references public.users(id),
                    exchange_account_id integer not null references public.exchange_accounts(id),
                    asset varchar not null,
                    strategy_key varchar not null,
                    name varchar not null default 'Cash & Funding',
                    status varchar not null default 'ACTIVE',
                    config json null,
                    allocated_capital_usdc double precision not null default 0,
                    total_quantity double precision not null default 0,
                    entry_spot_px double precision null,
                    entry_perp_px double precision null,
                    realized_pnl_usdc double precision null,
                    created_at timestamptz not null default now(),
                    updated_at timestamptz null,
                    closed_at timestamptz null
                )
                """
            )
        )
        await conn.execute(
            text("create index if not exists idx_strategies_user_id on public.strategies(user_id)")
        )
        await conn.execute(
            text("create index if not exists idx_strategies_asset on public.strategies(asset)")
        )
        await conn.execute(
            text(
                """
                create table if not exists public.strategy_positions (
                    id serial primary key,
                    strategy_id integer not null references public.strategies(id),
                    allocated_capital_usdc double precision not null,
                    quantity double precision not null,
                    entry_spot_px double precision null,
                    entry_perp_px double precision null,
                    created_at timestamptz not null default now()
                )
                """
            )
        )
        await conn.execute(
            text("create index if not exists idx_strategy_positions_strategy_id on public.strategy_positions(strategy_id)")
        )
        await conn.execute(
            text(
                """
                create table if not exists public.equity_snapshots (
                    id serial primary key,
                    strategy_id integer not null references public.strategies(id),
                    snapshot_date date not null,
                    equity_usdc double precision not null,
                    funding_delta_usdc double precision not null default 0,
                    fees_delta_usdc double precision not null default 0,
                    run_id text null,
                    as_of timestamptz null,
                    created_at timestamptz not null default now()
                )
                """
            )
        )
        await conn.execute(
            text("alter table public.equity_snapshots add column if not exists funding_delta_usdc double precision not null default 0")
        )
        await conn.execute(
            text("alter table public.equity_snapshots add column if not exists fees_delta_usdc double precision not null default 0")
        )
        await conn.execute(
            text("alter table public.equity_snapshots add column if not exists run_id text null")
        )
        await conn.execute(
            text("alter table public.equity_snapshots add column if not exists as_of timestamptz null")
        )
        await conn.execute(
            text("alter table public.equity_snapshots drop column if exists spot_px")
        )
        await conn.execute(
            text("alter table public.equity_snapshots drop column if exists perp_px")
        )
        await conn.execute(
            text("alter table public.equity_snapshots drop column if exists quantity")
        )
        await conn.execute(
            text("alter table public.equity_snapshots drop column if exists pnl_usdc")
        )
        await conn.execute(
            text("alter table public.equity_snapshots drop column if exists source")
        )
        await conn.execute(
            text("create index if not exists idx_equity_snapshots_strategy_id on public.equity_snapshots(strategy_id)")
        )
        await conn.execute(
            text(
                "create unique index if not exists ux_equity_snapshots_strategy_date on public.equity_snapshots(strategy_id, snapshot_date)"
            )
        )
        await conn.execute(
            text(
                """
                create table if not exists public.strategy_closures (
                    id serial primary key,
                    strategy_id integer not null references public.strategies(id),
                    started_at timestamptz not null,
                    closed_at timestamptz not null,
                    starting_capital_usdc double precision not null,
                    final_capital_usdc double precision not null,
                    pnl_usdc double precision not null,
                    apr_percent double precision not null,
                    fees_usdc double precision not null,
                    days_active integer not null,
                    created_at timestamptz not null default now()
                )
                """
            )
        )
        await conn.execute(
            text(
                "create unique index if not exists ux_strategy_closures_strategy_id on public.strategy_closures(strategy_id)"
            )
        )
        await conn.execute(
            text("create index if not exists idx_strategy_closures_closed_at on public.strategy_closures(closed_at)")
        )
        await conn.execute(
            text("alter table public.strategies add column if not exists name varchar")
        )
        await conn.execute(
            text("update public.strategies set name = 'Cash & Funding' where name is null")
        )
        await conn.execute(
            text("alter table public.strategies alter column name set default 'Cash & Funding'")
        )
        await conn.execute(
            text("alter table public.strategies alter column name set not null")
        )
        await conn.execute(
            text("alter table public.exchange_credentials add column if not exists exchange_account_id integer references public.exchange_accounts(id)")
        )
        await conn.execute(
            text("alter table public.exchange_credentials add column if not exists disabled_at timestamptz null")
        )
        await conn.execute(
            text("alter table public.strategies add column if not exists exchange_account_id integer references public.exchange_accounts(id)")
        )
        await conn.execute(
            text("alter table public.strategies add column if not exists strategy_key varchar")
        )
        await conn.execute(
            text("alter table public.strategies add column if not exists config json")
        )
        await conn.execute(
            text("alter table public.strategies add column if not exists closed_at timestamptz null")
        )
        await conn.execute(
            text("update public.strategies set strategy_key = 'cash_funding' where strategy_key is null")
        )
        await conn.execute(
            text("alter table public.strategies alter column strategy_key set not null")
        )
        await conn.execute(
            text(
                """
                insert into public.exchange_accounts (user_id, exchange_name, created_at)
                select distinct ec.user_id, ec.exchange_name, now()
                from public.exchange_credentials ec
                where not exists (
                    select 1 from public.exchange_accounts ea
                    where ea.user_id = ec.user_id and ea.exchange_name = ec.exchange_name
                )
                """
            )
        )
        await conn.execute(
            text(
                """
                insert into public.exchange_accounts (user_id, exchange_name, created_at)
                select distinct s.user_id, 'deribit', now()
                from public.strategies s
                where not exists (
                    select 1 from public.exchange_accounts ea
                    where ea.user_id = s.user_id and ea.exchange_name = 'deribit'
                )
                """
            )
        )
        await conn.execute(
            text(
                """
                update public.exchange_credentials ec
                set exchange_account_id = ea.id
                from public.exchange_accounts ea
                where ec.exchange_account_id is null
                  and ea.user_id = ec.user_id
                  and ea.exchange_name = ec.exchange_name
                """
            )
        )
        await conn.execute(
            text("alter table public.exchange_credentials alter column exchange_account_id set not null")
        )
        await conn.execute(
            text(
                """
                update public.strategies s
                set exchange_account_id = ea.id
                from public.exchange_accounts ea
                where s.exchange_account_id is null
                  and ea.user_id = s.user_id
                  and ea.exchange_name = 'deribit'
                """
            )
        )
        await conn.execute(
            text("alter table public.strategies alter column exchange_account_id set not null")
        )
        await conn.execute(
            text(
                "create index if not exists idx_strategies_exchange_account_id on public.strategies(exchange_account_id)"
            )
        )
        await conn.execute(
            text("drop index if exists ux_strategies_user_asset_active")
        )
        await conn.execute(
            text(
                "create unique index if not exists ux_strategies_account_asset_active on public.strategies(exchange_account_id, asset) where status = 'ACTIVE'"
            )
        )


if __name__ == "__main__":
    asyncio.run(migrate())
