import asyncio
import os
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.engine.url import make_url

from app.services.exchange_service import ExchangeService
from app.services.strategies.registry import get_strategy_registry
from core.config import settings
from core.database import AsyncSessionLocal
from core.enums import StrategyStatus
from core.models import ExchangeAccount, Strategy


async def run_balance_cache():
    run_at = datetime.now(timezone.utc)
    run_id = run_at.strftime("%Y%m%d%H%M%S")
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
        f"[balance_cache] start run_id={run_id} run_at={run_at.isoformat()} "
        f"db_host={db_host} db_name={db_name} db_user={db_user}"
    )

    async with AsyncSessionLocal() as db:
        exchange_service = ExchangeService(db)
        strategy_registry = get_strategy_registry()
        default_strategy_key = next(iter(strategy_registry), "")
        result = await db.execute(
            select(ExchangeAccount).where(ExchangeAccount.disabled_at.is_(None))
        )
        accounts = result.scalars().all()
        total_accounts = len(accounts)
        updated = 0
        skipped_missing_exchange = 0
        skipped_exception = 0

        if not accounts:
            print(f"[balance_cache] no active exchange accounts, run_id={run_id}")
            return

        account_ids = [account.id for account in accounts]
        strategy_result = await db.execute(
            select(Strategy)
            .where(
                Strategy.status == StrategyStatus.ACTIVE,
                Strategy.exchange_account_id.in_(account_ids),
            )
            .order_by(Strategy.exchange_account_id.asc(), Strategy.created_at.asc())
        )
        active_strategies = strategy_result.scalars().all()
        strategy_key_by_account = {}
        for strategy in active_strategies:
            if strategy.exchange_account_id not in strategy_key_by_account:
                strategy_key_by_account[strategy.exchange_account_id] = str(
                    strategy.strategy_key or default_strategy_key
                )

        if debug:
            print(
                f"[balance_cache] accounts={total_accounts} "
                f"accounts_with_active_strategy={len(strategy_key_by_account)} run_id={run_id}"
            )

        for account in accounts:
            exchange = await exchange_service.get_exchange_client_by_account(account.id)
            if not exchange:
                skipped_missing_exchange += 1
                if debug:
                    print(
                        f"[balance_cache] skip account_id={account.id} reason=exchange_not_configured "
                        f"exchange={account.exchange_name} run_id={run_id}"
                    )
                continue
            try:
                strategy_key = strategy_key_by_account.get(account.id) or default_strategy_key
                strategy_impl = strategy_registry.get(strategy_key) or strategy_registry.get(default_strategy_key)
                if not strategy_impl:
                    raise ValueError("strategy_not_configured")
                adapter = exchange_service.get_exchange_adapter(account.exchange_name)
                balance = await strategy_impl.fetch_usdc_balance(exchange, adapter)
                account.cached_balance_usdc = float(balance or 0.0)
                account.balance_updated_at = datetime.now(timezone.utc)
                await db.commit()
                updated += 1
                if debug:
                    print(
                        f"[balance_cache] updated account_id={account.id} exchange={account.exchange_name} "
                        f"strategy_key={strategy_key} balance={account.cached_balance_usdc} run_id={run_id}"
                    )
            except Exception as e:
                await db.rollback()
                skipped_exception += 1
                if debug:
                    print(
                        f"[balance_cache] error account_id={account.id} exchange={account.exchange_name} "
                        f"err={type(e).__name__}:{e} run_id={run_id}"
                    )
            finally:
                await exchange.close()

        print(
            f"[balance_cache] done run_id={run_id} accounts={total_accounts} updated={updated} "
            f"skipped_missing_exchange={skipped_missing_exchange} skipped_exception={skipped_exception}"
        )


if __name__ == "__main__":
    asyncio.run(run_balance_cache())
