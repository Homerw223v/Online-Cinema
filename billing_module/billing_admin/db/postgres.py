from core.config import settings
from db.models import Base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema


async def create_database() -> None:
    async with engine.begin() as conn:
        await conn.execute(CreateSchema("billing", if_not_exists=True))
        await conn.run_sync(Base.metadata.create_all)


async def purge_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


engine = create_async_engine(
    str(settings.postgres.dsn),
    future=True,
    poolclass=NullPool,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
