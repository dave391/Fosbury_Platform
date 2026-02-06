import asyncio

from core.database import Base
from core.database import engine
from core.models import ExchangeAccount
from core.models import ExchangeCredentials
from core.models import EquitySnapshot
from core.models import Strategy
from core.models import StrategyPosition
from core.models import User


async def init_models():
    async with engine.begin() as conn:
        print("Drop e creazione tabelle su Supabase in corso...")
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        print("Tabelle create con successo!")


_ = (User, ExchangeAccount, ExchangeCredentials, Strategy, StrategyPosition, EquitySnapshot)


if __name__ == "__main__":
    asyncio.run(init_models())
