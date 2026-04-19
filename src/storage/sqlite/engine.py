from functools import lru_cache
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config.settings import get_settings
from src.storage.sqlite.models import Base
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


@lru_cache
def get_engine() -> AsyncEngine:
    """Возвращает синглтон async SQLAlchemy engine для sqlite."""
    settings = get_settings()
    db_path = Path(settings.sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite+aiosqlite:///{db_path}"
    logger.info(f"Создание SQLite engine: {url}")
    return create_async_engine(url)


@lru_cache
def _session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


def get_session() -> AsyncSession:
    """Возвращает новую async-сессию. Юзать как `async with get_session() as session:`."""
    return _session_factory()()


async def init_db() -> None:
    """Создаёт таблицы, если их нет. Вызывать на старте приложения."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("SQLite: схема готова")
