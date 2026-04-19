from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from src.config.settings import get_settings
from src.storage.sqlite.engine import get_session
from src.storage.sqlite.models import User
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


async def get_user_model(user_id: int) -> str:
    """Модель, выбранная юзером. Если записи нет — settings.default_model."""
    settings = get_settings()
    async with get_session() as session:
        result = await session.execute(select(User.model).where(User.user_id == user_id))
        model = result.scalar_one_or_none()
    return model or settings.default_model


async def set_user_model(user_id: int, model: str) -> None:
    """Сохранить выбор модели. Валидирует по settings.available_models. Upsert по user_id."""
    settings = get_settings()
    if model not in settings.available_models:
        raise ValueError(f"Модель {model!r} не входит в available_models: {settings.available_models}")

    stmt = (
        sqlite_insert(User)
        .values(user_id=user_id, model=model)
        .on_conflict_do_update(index_elements=[User.user_id], set_={"model": model})
    )
    async with get_session() as session:
        await session.execute(stmt)
        await session.commit()
    logger.debug(f"user_id={user_id}: модель установлена в {model}")
