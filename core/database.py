from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from core.config import settings

# Crea il motore di connessione
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Configura la sessione (lo strumento che useremo per fare query)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Classe base per i modelli
Base = declarative_base()


# Funzione per ottenere il DB nelle rotte API (Dependency Injection)
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
