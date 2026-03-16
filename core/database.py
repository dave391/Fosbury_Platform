from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from core.config import settings

# Crea il motore di connessione
database_url = make_url(settings.DATABASE_URL)
if database_url.drivername in ("postgresql", "postgres"):
    database_url = database_url.set(drivername="postgresql+asyncpg")
engine = create_async_engine(
    database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=300,
)

# Configura la sessione (lo strumento che useremo per fare query)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Classe base per i modelli
Base = declarative_base()


# Funzione per ottenere il DB nelle rotte API (Dependency Injection)
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
