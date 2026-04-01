from abc import ABC, abstractmethod
from typing import Protocol, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import Strategy


class StrategyAdapter(ABC):
    key: str
    name: str

    @abstractmethod
    def get_allowed_assets(self, exchange_id: str) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def get_min_capital(self) -> float:
        raise NotImplementedError

    @abstractmethod
    async def fetch_usdc_balance(self, exchange, adapter) -> float:
        raise NotImplementedError

    @abstractmethod
    async def start(
        self,
        db: AsyncSession,
        exchange,
        user_id: int,
        exchange_account_id: int,
        asset: str,
        capital_usdc: float,
    ) -> Strategy:
        raise NotImplementedError

    @abstractmethod
    async def add(self, db: AsyncSession, exchange, strategy: Strategy, added_amount_usdc: float) -> Strategy:
        raise NotImplementedError

    @abstractmethod
    async def remove(self, db: AsyncSession, exchange, strategy: Strategy, remove_amount_usdc: float) -> float:
        raise NotImplementedError

    @abstractmethod
    async def stop(self, db: AsyncSession, exchange, strategy: Strategy) -> float:
        raise NotImplementedError

    async def get_snapshot_equity_usdc(
        self,
        exchange,
        adapter,
        strategy: Strategy,
        base_equity_usdc: float,
        funding_delta_usdc: float,
        fees_delta_usdc: float,
    ) -> float:
        _ = exchange
        _ = adapter
        _ = strategy
        return float(base_equity_usdc + (funding_delta_usdc - fees_delta_usdc))


class StrategyRegistry(Protocol):
    def get(self, key: str) -> Optional[StrategyAdapter]:
        ...
