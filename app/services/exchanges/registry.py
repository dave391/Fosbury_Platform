from typing import Dict
from core.enums import ExchangeName
from app.services.exchanges.base import ExchangeAdapter
from app.services.exchanges.deribit import DeribitExchange
from app.services.exchanges.bitmex import BitmexExchange


def get_exchange_registry() -> Dict[str, ExchangeAdapter]:
    return {
        ExchangeName.DERIBIT: DeribitExchange(),
        ExchangeName.BITMEX: BitmexExchange(),
    }
