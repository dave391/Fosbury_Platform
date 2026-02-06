from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple


class ExchangeAdapter(ABC):
    @abstractmethod
    async def get_client(self, api_key: str, api_secret: str):
        raise NotImplementedError

    @abstractmethod
    async def validate_credentials(self, api_key: str, api_secret: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def fetch_active_currencies(self, exchange) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_transaction_logs(
        self, exchange, currency: str, start_ms: int, end_ms: int
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_strategy_deltas(
        self, exchange, strategy: Any, start_ms: int, end_ms: int
    ) -> Tuple[float, float]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_quote_balance(self, exchange, quote: str) -> float:
        raise NotImplementedError
