from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func
from core.models import Strategy, EquitySnapshot, StrategyClosure, ExchangeAccount
from core.enums import StrategyStatus, ExchangeName
from core.constants import MIN_ADD_CAPITAL_USDC, MIN_REMOVE_CAPITAL_USDC
from typing import List, Optional, Dict, Any
from app.services.exchange_service import ExchangeService
from app.services.strategies.registry import get_strategy_registry, DEFAULT_STRATEGY_KEY
from datetime import date, datetime, timezone, time
import asyncio
from uuid import uuid4
from importlib import import_module

class StrategyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.exchange_service = ExchangeService(db)
        self.strategy_registry = get_strategy_registry()
        self.default_strategy_key = DEFAULT_STRATEGY_KEY

    def get_available_strategies(self) -> List[Dict[str, str]]:
        return [
            {"key": key, "name": getattr(strategy_impl, "name", key)}
            for key, strategy_impl in self.strategy_registry.items()
        ]

    async def get_connected_exchange_names(self, user_id: int) -> List[str]:
        credentials = await self.exchange_service.get_configured_exchanges(user_id)
        exchanges = []
        for row in credentials:
            name = row.get("exchange_name") if row else None
            if name and name not in exchanges:
                exchanges.append(name)
        return exchanges

    async def get_active_strategies(self, user_id: int) -> List[Strategy]:
        result = await self.db.execute(
            select(Strategy)
            .where(Strategy.user_id == user_id, Strategy.status == StrategyStatus.ACTIVE)
            .order_by(Strategy.created_at.desc())
        )
        return result.scalars().all()

    async def get_strategy_by_id(self, user_id: int, strategy_id: int) -> Optional[Strategy]:
        result = await self.db.execute(
            select(Strategy)
            .where(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id,
                Strategy.status == StrategyStatus.ACTIVE
            )
        )
        return result.scalars().first()

    async def get_closed_strategies(self, user_id: int) -> List[Strategy]:
        result = await self.db.execute(
            select(Strategy)
            .where(Strategy.user_id == user_id, Strategy.status == StrategyStatus.CLOSED)
            .order_by(Strategy.closed_at.desc(), Strategy.created_at.desc())
        )
        return result.scalars().all()

    async def get_strategy_closures(self, strategy_ids: List[int]) -> List[StrategyClosure]:
        if not strategy_ids:
            return []
        result = await self.db.execute(
            select(StrategyClosure)
            .where(StrategyClosure.strategy_id.in_(strategy_ids))
        )
        return result.scalars().all()

    async def get_equity_snapshots(self, strategy_ids: List[int]) -> List[EquitySnapshot]:
        if not strategy_ids:
            return []
        result = await self.db.execute(
            select(EquitySnapshot)
            .where(EquitySnapshot.strategy_id.in_(strategy_ids))
            .order_by(EquitySnapshot.snapshot_date.asc())
        )
        return result.scalars().all()

    async def build_active_strategy_rows(
        self,
        user_id: int,
        active_strategies: List[Strategy],
        scope_strategies: Optional[List[Strategy]] = None,
    ) -> Dict[str, Any]:
        today = date.today()
        scope = scope_strategies if scope_strategies is not None else active_strategies
        if not active_strategies:
            return {"rows": [], "strategy_stats": {}}
        account_ids = {strategy.exchange_account_id for strategy in active_strategies}
        accounts_by_id = {}
        if account_ids:
            accounts_result = await self.db.execute(
                select(ExchangeAccount).where(ExchangeAccount.id.in_(account_ids))
            )
            accounts_by_id = {account.id: account for account in accounts_result.scalars().all()}

        available_by_pair = {}
        if accounts_by_id:
            semaphore = asyncio.Semaphore(4)
            timeout_seconds = 6

            async def fetch_balance(account_id: int, strategy_key: str):
                async with semaphore:
                    account = accounts_by_id.get(account_id)
                    if not account:
                        return account_id, strategy_key, 0.0
                    exchange = await self.exchange_service.get_exchange_client_by_account(account_id)
                    if not exchange:
                        return account_id, strategy_key, 0.0
                    try:
                        strategy_impl = self._get_strategy_impl(strategy_key)
                        adapter = self.exchange_service.get_exchange_adapter(account.exchange_name)
                        balance = await asyncio.wait_for(
                            strategy_impl.fetch_usdc_balance(exchange, adapter),
                            timeout=timeout_seconds,
                        )
                        return account_id, strategy_key, balance
                    except Exception:
                        return account_id, strategy_key, 0.0
                    finally:
                        await exchange.close()

            account_strategy_pairs = {
                (
                    strategy.exchange_account_id,
                    str(strategy.strategy_key or self.default_strategy_key),
                )
                for strategy in active_strategies
            }
            tasks = [
                fetch_balance(account_id, strategy_key)
                for account_id, strategy_key in account_strategy_pairs
            ]
            for account_id, strategy_key, balance in await asyncio.gather(*tasks):
                available_by_pair[(account_id, strategy_key)] = balance

        rows = []
        for strategy in active_strategies:
            days_active = max(1, (today - strategy.created_at.date()).days + 1)
            account = accounts_by_id.get(strategy.exchange_account_id)
            strategy_key = str(strategy.strategy_key or self.default_strategy_key)
            strategy_impl = self._get_strategy_impl(strategy_key)
            quote_currency = self._get_quote_currency(strategy_impl, account.exchange_name if account else None)
            rows.append(
                {
                    "id": strategy.id,
                    "asset": strategy.asset,
                    "name": strategy.name,
                    "allocated_capital_usdc": strategy.allocated_capital_usdc,
                    "current_capital_usdc": strategy.allocated_capital_usdc,
                    "pnl_usdc": 0.0,
                    "apr_percent": 0.0,
                    "roi_percent": 0.0,
                    "days_active": days_active,
                    "reduce_max_usdc": max(0.0, strategy.allocated_capital_usdc - 1),
                    "exchange_account_id": strategy.exchange_account_id,
                    "exchange_name": account.exchange_name if account else None,
                    "exchange_available_usdc": available_by_pair.get(
                        (strategy.exchange_account_id, strategy_key), 0.0
                    ),
                    "quote_currency": quote_currency,
                }
            )

        strategy_stats = {}

        snapshot_stats = {}
        if rows:
            strategy_ids = [row["id"] for row in rows]
            snapshot_result = await self.db.execute(
                select(EquitySnapshot)
                .where(EquitySnapshot.strategy_id.in_(strategy_ids))
                .order_by(EquitySnapshot.snapshot_date.asc(), EquitySnapshot.created_at.asc())
            )
            for snap in snapshot_result.scalars().all():
                stats = snapshot_stats.setdefault(
                    snap.strategy_id,
                    {"pnl_usdc": 0.0, "last_snapshot": None},
                )
                stats["pnl_usdc"] += (snap.funding_delta_usdc or 0.0) - (snap.fees_delta_usdc or 0.0)
                stats["last_snapshot"] = snap

        for row in rows:
            stats = snapshot_stats.get(row["id"])
            snap = stats["last_snapshot"] if stats else None
            if snap:
                current_capital = snap.equity_usdc
                pnl_usdc = stats["pnl_usdc"] if stats else 0.0
            else:
                current_capital = row["allocated_capital_usdc"]
                pnl_usdc = 0.0
            row["current_capital_usdc"] = current_capital
            row["reduce_max_usdc"] = max(0.0, current_capital - 1)
            row["pnl_usdc"] = pnl_usdc
            if row["allocated_capital_usdc"] > 0:
                row["roi_percent"] = (pnl_usdc / row["allocated_capital_usdc"]) * 100
            else:
                row["roi_percent"] = 0.0
            if row["allocated_capital_usdc"] > 0 and row["days_active"] > 0:
                row["apr_percent"] = (pnl_usdc / row["allocated_capital_usdc"]) * (365 / row["days_active"]) * 100
            else:
                row["apr_percent"] = 0.0
            strategy_stats[row["id"]] = {
                "pnl_usdc": pnl_usdc,
                "current_capital": current_capital,
            }

        return {"rows": rows, "strategy_stats": strategy_stats}

    async def get_strategy_page_data(
        self,
        user_id: int,
        exchange_name: str = ExchangeName.DERIBIT,
        connected_exchanges: Optional[List[str]] = None,
        strategy_key: Optional[str] = None,
        exchange_account_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Prepares data for the strategy page, including active strategies and user balance.
        """
        if isinstance(exchange_name, ExchangeName):
            exchange_name = exchange_name.value
        if connected_exchanges is None:
            connected_exchanges = await self.get_connected_exchange_names(user_id)
        if connected_exchanges and exchange_name not in connected_exchanges:
            exchange_name = connected_exchanges[0]
        strategies = await self.get_active_strategies(user_id)
        
        usdc_balance = 0.0
        strategy_impl = self._get_strategy_impl(strategy_key)
        selected_strategy_key = str(getattr(strategy_impl, "key", "") or self.default_strategy_key)
        allowed_assets = strategy_impl.get_allowed_assets(exchange_name)
        min_capital_usd = strategy_impl.get_min_capital()
        quote_currency = self._get_quote_currency(strategy_impl, exchange_name)
        exchange_accounts = await self.exchange_service.get_user_exchange_accounts(user_id, exchange_name)
        has_credentials = bool(exchange_accounts)
        selected_account = None
        if exchange_account_id is not None:
            selected_account = next(
                (account for account in exchange_accounts if account["id"] == exchange_account_id),
                None,
            )
        if selected_account is None and exchange_accounts:
            selected_account = exchange_accounts[0]

        if selected_account:
            exchange = await self.exchange_service.get_exchange_client_by_account(selected_account["id"])
            if exchange:
                try:
                    adapter = self.exchange_service.get_exchange_adapter(exchange_name)
                    usdc_balance = await strategy_impl.fetch_usdc_balance(exchange, adapter)
                except Exception:
                    pass
                finally:
                    await exchange.close()
                
        return {
            "user_id": user_id,
            "strategies": strategies,
            "usdc_balance": usdc_balance,
            "has_credentials": has_credentials,
            "allowed_assets": allowed_assets,
            "min_capital_usd": min_capital_usd,
            "exchange_name": exchange_name,
            "quote_currency": quote_currency,
            "strategy_key": selected_strategy_key,
            "available_strategies": self.get_available_strategies(),
            "exchange_accounts": exchange_accounts,
            "exchange_account_id": selected_account["id"] if selected_account else None,
        }

    async def _get_exchange_or_raise(self, exchange_account_id: int):
        exchange = await self.exchange_service.get_exchange_client_by_account(exchange_account_id)
        if not exchange:
            raise ValueError("Exchange credentials missing.")
        return exchange

    def _get_strategy_impl(self, strategy_key: Optional[str] = None):
        key = str(strategy_key or self.default_strategy_key).strip() or self.default_strategy_key
        strategy_impl = self.strategy_registry.get(key)
        if not strategy_impl:
            raise ValueError(f"Strategy '{key}' not available.")
        return strategy_impl

    def _get_quote_currency(self, strategy_impl, exchange_name: Optional[str]) -> str:
        try:
            module_name = strategy_impl.__class__.__module__
            rules_module_name = f"{module_name.rsplit('.', 1)[0]}.rules"
            rules_module = import_module(rules_module_name)
            get_exchange_rules = getattr(rules_module, "get_exchange_rules", None)
            if callable(get_exchange_rules):
                rules = get_exchange_rules(str(exchange_name or "").lower())
                quote = (rules or {}).get("quote")
                if quote:
                    return quote
        except Exception:
            pass
        return "USDC"

    async def start_strategy(
        self,
        user_id: int,
        asset: str,
        capital_usdc: float,
        exchange_name: str = ExchangeName.DERIBIT,
        strategy_key: Optional[str] = None,
        exchange_account_id: Optional[int] = None,
    ) -> Strategy:
        if not str(strategy_key or "").strip():
            raise ValueError("Strategy selection is required.")
        strategy_impl = self._get_strategy_impl(strategy_key)
        selected_strategy_key = str(getattr(strategy_impl, "key", "") or self.default_strategy_key)
        if exchange_account_id is None:
            raise ValueError("Exchange account selection is required.")
        account = await self.exchange_service.get_exchange_account(user_id, exchange_account_id)
        if not account:
            raise ValueError("Invalid exchange account.")
        exchange_name = account.exchange_name
        allowed_assets = strategy_impl.get_allowed_assets(exchange_name)
        if allowed_assets and asset not in allowed_assets:
            raise ValueError(f"Invalid asset. Supported assets: {', '.join(allowed_assets)}")
        min_capital_usd = strategy_impl.get_min_capital()
        if capital_usdc < min_capital_usd:
            raise ValueError(f"Minimum capital is {min_capital_usd} USD.")

        active_on_account_result = await self.db.execute(
            select(Strategy).where(
                Strategy.exchange_account_id == account.id,
                Strategy.status == StrategyStatus.ACTIVE,
            )
        )
        active_on_account = active_on_account_result.scalars().all()
        if any(
            str(strategy.strategy_key or self.default_strategy_key) != selected_strategy_key
            for strategy in active_on_account
        ):
            raise ValueError("Another strategy is already active on this account.")

        duplicate_result = await self.db.execute(
            select(Strategy).where(
                Strategy.exchange_account_id == account.id,
                Strategy.asset == asset,
                Strategy.status == StrategyStatus.ACTIVE,
            )
        )
        if duplicate_result.scalars().first():
            raise ValueError("Strategy already active for this asset.")

        exchange = await self._get_exchange_or_raise(account.id)

        try:
            adapter = self.exchange_service.get_exchange_adapter(account.exchange_name)
            usdc_balance = await strategy_impl.fetch_usdc_balance(exchange, adapter)
            if capital_usdc > usdc_balance:
                raise ValueError(f"Insufficient USDC balance. Available: {usdc_balance}, Required: {capital_usdc}")

            strategy = await strategy_impl.start(self.db, exchange, user_id, account.id, asset, capital_usdc)
            await self.db.commit()
            return strategy
        except Exception:
            await self.db.rollback()
            raise
        finally:
            await exchange.close()

    async def add_capital(self, user_id: int, strategy_id: int, added_amount_usdc: float) -> Strategy:
        if added_amount_usdc < MIN_ADD_CAPITAL_USDC:
            raise ValueError(f"Minimum amount is {MIN_ADD_CAPITAL_USDC} USDC.")

        strategy = await self.get_strategy_by_id(user_id, strategy_id)
        if not strategy:
            raise ValueError("Strategy not found.")

        exchange = await self._get_exchange_or_raise(strategy.exchange_account_id)

        try:
            adapter = self.exchange_service.get_exchange_adapter(exchange.id)
            strategy_impl = self._get_strategy_impl(strategy.strategy_key)
            usdc_balance = await strategy_impl.fetch_usdc_balance(exchange, adapter)
            if added_amount_usdc > usdc_balance:
                raise ValueError(f"Insufficient USDC balance. Available: {usdc_balance}, Required: {added_amount_usdc}")

            await strategy_impl.add(self.db, exchange, strategy, added_amount_usdc)
            await self.db.commit()
            return strategy
        except Exception:
            await self.db.rollback()
            raise
        finally:
            await exchange.close()

    async def remove_capital(self, user_id: int, strategy_id: int, remove_amount_usdc: float) -> float:
        if remove_amount_usdc < MIN_REMOVE_CAPITAL_USDC:
            raise ValueError(f"Minimum amount is {MIN_REMOVE_CAPITAL_USDC} USDC.")

        strategy = await self.get_strategy_by_id(user_id, strategy_id)
        if not strategy:
            raise ValueError("Strategy not found.")

        exchange = await self._get_exchange_or_raise(strategy.exchange_account_id)

        try:
            strategy_impl = self._get_strategy_impl(strategy.strategy_key)
            starting_capital = strategy.allocated_capital_usdc
            qty_removed = await strategy_impl.remove(self.db, exchange, strategy, remove_amount_usdc)
            if strategy.status == StrategyStatus.CLOSED:
                if strategy.closed_at is None:
                    strategy.closed_at = datetime.now(timezone.utc)
                await self._ensure_close_day_snapshot(exchange, strategy, strategy.closed_at, starting_capital)
                await self.ensure_strategy_closure(strategy, starting_capital)
            await self.db.commit()
            return qty_removed
        except Exception:
            await self.db.rollback()
            raise
        finally:
            await exchange.close()

    async def stop_strategy(self, user_id: int, strategy_id: int) -> float:
        strategy = await self.get_strategy_by_id(user_id, strategy_id)
        if not strategy:
            raise ValueError("Strategy not found.")

        exchange = await self._get_exchange_or_raise(strategy.exchange_account_id)

        try:
            strategy_impl = self._get_strategy_impl(strategy.strategy_key)
            starting_capital = strategy.allocated_capital_usdc
            qty_closed = await strategy_impl.stop(self.db, exchange, strategy)
            if strategy.status == StrategyStatus.CLOSED:
                if strategy.closed_at is None:
                    strategy.closed_at = datetime.now(timezone.utc)
                await self._ensure_close_day_snapshot(exchange, strategy, strategy.closed_at, starting_capital)
                await self.ensure_strategy_closure(strategy, starting_capital)
            await self.db.commit()
            return qty_closed
        except Exception:
            await self.db.rollback()
            raise
        finally:
            await exchange.close()

    async def _ensure_close_day_snapshot(
        self,
        exchange,
        strategy: Strategy,
        closed_at: datetime,
        starting_capital_usdc: float,
    ) -> None:
        account_result = await self.db.execute(
            select(ExchangeAccount).where(ExchangeAccount.id == strategy.exchange_account_id)
        )
        account = account_result.scalars().first()
        if not account or not account.exchange_name:
            return

        adapter = self.exchange_service.get_exchange_adapter(account.exchange_name)
        snapshot_day = closed_at.date()
        start_dt = datetime.combine(snapshot_day, time.min, tzinfo=timezone.utc)
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(closed_at.timestamp() * 1000)
        funding_delta, fees_delta = await adapter.fetch_strategy_deltas(exchange, strategy, start_ms, end_ms)

        base_result = await self.db.execute(
            select(EquitySnapshot)
            .where(
                EquitySnapshot.strategy_id == strategy.id,
                EquitySnapshot.snapshot_date < snapshot_day,
            )
            .order_by(EquitySnapshot.snapshot_date.desc())
        )
        base_snapshot = base_result.scalars().first()
        base_equity = base_snapshot.equity_usdc if base_snapshot else starting_capital_usdc
        equity_usdc = base_equity + (funding_delta - fees_delta)

        existing_result = await self.db.execute(
            select(EquitySnapshot).where(
                EquitySnapshot.strategy_id == strategy.id,
                EquitySnapshot.snapshot_date == snapshot_day,
            )
        )
        existing = existing_result.scalars().first()
        run_id = f"stop_{uuid4().hex}"
        if existing:
            existing.equity_usdc = equity_usdc
            existing.funding_delta_usdc = funding_delta
            existing.fees_delta_usdc = fees_delta
            existing.run_id = run_id
            existing.as_of = closed_at
        else:
            self.db.add(
                EquitySnapshot(
                    strategy_id=strategy.id,
                    snapshot_date=snapshot_day,
                    equity_usdc=equity_usdc,
                    funding_delta_usdc=funding_delta,
                    fees_delta_usdc=fees_delta,
                    run_id=run_id,
                    as_of=closed_at,
                )
            )

    async def ensure_strategy_closure(self, strategy: Strategy, starting_capital_usdc: float) -> None:
        result = await self.db.execute(
            select(StrategyClosure).where(StrategyClosure.strategy_id == strategy.id)
        )
        existing = result.scalars().first()
        if existing:
            return

        closed_at = strategy.closed_at or datetime.now(timezone.utc)
        started_at = strategy.created_at
        days_active = max(1, (closed_at.date() - started_at.date()).days + 1)

        totals_result = await self.db.execute(
            select(
                func.sum(EquitySnapshot.funding_delta_usdc).label("funding_total"),
                func.sum(EquitySnapshot.fees_delta_usdc).label("fees_total"),
            )
            .where(EquitySnapshot.strategy_id == strategy.id)
        )
        totals = totals_result.first()
        funding_total = float(totals.funding_total or 0.0) if totals else 0.0
        fees_total = float(totals.fees_total or 0.0) if totals else 0.0

        realized_pnl = float(strategy.realized_pnl_usdc or 0.0)
        pnl_usdc = realized_pnl + funding_total - fees_total
        if starting_capital_usdc > 0 and days_active > 0:
            apr_percent = (pnl_usdc / starting_capital_usdc) * (365 / days_active) * 100
        else:
            apr_percent = 0.0
        final_capital_usdc = starting_capital_usdc + pnl_usdc

        self.db.add(
            StrategyClosure(
                strategy_id=strategy.id,
                started_at=started_at,
                closed_at=closed_at,
                starting_capital_usdc=starting_capital_usdc,
                final_capital_usdc=final_capital_usdc,
                pnl_usdc=pnl_usdc,
                apr_percent=apr_percent,
                fees_usdc=fees_total,
                days_active=days_active,
            )
        )
