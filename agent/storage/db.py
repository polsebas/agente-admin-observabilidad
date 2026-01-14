from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from agent.config import AdminAgentConfig

_config = AdminAgentConfig()

# Construir URL de conexión
# postgres_password puede ser vacío
auth = f"{_config.postgres_user}:{_config.postgres_password}" if _config.postgres_password else _config.postgres_user
db_url = f"postgresql+asyncpg://{auth}@{_config.postgres_host}:{_config.postgres_port}/{_config.postgres_db}"

engine = create_async_engine(db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
