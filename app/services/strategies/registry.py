from app.services.strategies.base import StrategyRegistry
from app.services.strategies.cash_funding import CashFundingStrategy
from app.services.strategies.cash_funding.rules import STRATEGY_KEY


DEFAULT_STRATEGY_KEY = STRATEGY_KEY


def get_strategy_registry() -> StrategyRegistry:
    return {
        STRATEGY_KEY: CashFundingStrategy(),
    }
