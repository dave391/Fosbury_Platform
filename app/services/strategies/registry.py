from app.services.strategies.base import StrategyRegistry
from app.services.strategies.cash_funding import CashFundingStrategy
from app.services.strategies.cash_funding.rules import STRATEGY_KEY as CF_KEY
from app.services.strategies.hlp import HLPStrategy
from app.services.strategies.nv1 import NV1Strategy
from app.services.strategies.nv1.rules import STRATEGY_KEY as NV1_KEY


def get_strategy_registry() -> StrategyRegistry:
    return {
        CF_KEY: CashFundingStrategy(),
        NV1_KEY: NV1Strategy(),
        HLPStrategy.key: HLPStrategy(),
    }
