from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import Strategy
from app.services.exchanges.registry import get_exchange_registry
from app.services.strategies.base import StrategyAdapter
from app.services.strategies.nv1.logic import start, add, remove, stop
from app.services.strategies.nv1.rules import STRATEGY_KEY, STRATEGY_NAME, MIN_CAPITAL_USD, get_exchange_rules


class NV1Strategy(StrategyAdapter):
    key = STRATEGY_KEY
    name = STRATEGY_NAME

    def _get_adapter(self, exchange):
        exchange_id = str(getattr(exchange, "id", "") or "").lower()
        adapter = get_exchange_registry().get(exchange_id)
        if adapter is None:
            raise ValueError(f"Exchange non supportato per NV1: {exchange_id}")
        return adapter

    def get_allowed_assets(self, exchange_id: str) -> List[str]:
        rules = get_exchange_rules(str(exchange_id or "").lower())
        return rules.get("assets") or []

    def get_min_capital(self) -> float:
        return float(MIN_CAPITAL_USD)

    async def fetch_usdc_balance(self, exchange, adapter) -> float:
        exchange_id = str(getattr(exchange, "id", "") or "").lower()
        rules = get_exchange_rules(exchange_id)
        quote = rules.get("quote") or "USDT"
        return await adapter.fetch_quote_balance(exchange, quote)

    async def start(
        self,
        db: AsyncSession,
        exchange,
        user_id: int,
        exchange_account_id: int,
        asset: str,
        capital_usdc: float,
    ) -> Strategy:
        adapter = self._get_adapter(exchange)
        available_balance = await self.fetch_usdc_balance(exchange, adapter)
        return await start(
            db,
            exchange,
            adapter,
            user_id,
            exchange_account_id,
            asset,
            capital_usdc,
            self.key,
            available_balance,
        )

    async def add(self, db: AsyncSession, exchange, strategy: Strategy, added_amount_usdc: float) -> Strategy:
        adapter = self._get_adapter(exchange)
        return await add(db, exchange, adapter, strategy, added_amount_usdc)

    async def remove(self, db: AsyncSession, exchange, strategy: Strategy, remove_amount_usdc: float) -> float:
        adapter = self._get_adapter(exchange)
        return await remove(db, exchange, adapter, strategy, remove_amount_usdc)

    async def stop(self, db: AsyncSession, exchange, strategy: Strategy) -> float:
        adapter = self._get_adapter(exchange)
        return await stop(db, exchange, adapter, strategy)


__all__ = ["NV1Strategy"]
