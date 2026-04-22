from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from src.config.settings import get_settings
from src.storage.sqlite.engine import get_session
from src.storage.sqlite.models import User
from src.utils.logger.LoggerFactory import LoggerFactory
from src.utils.metrics import db_queries_total

logger = LoggerFactory.get_logger(__name__)


async def get_user_model(user_id: int) -> str:
    """Модель, выбранная юзером. Если записи нет — settings.default_model."""
    settings = get_settings()
    try:
        async with get_session() as session:
            result = await session.execute(select(User.model).where(User.user_id == user_id))
            model = result.scalar_one_or_none()
        db_queries_total.labels(operation="get_user_model", status="success").inc()
    except Exception:
        db_queries_total.labels(operation="get_user_model", status="error").inc()
        raise
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
    try:
        async with get_session() as session:
            await session.execute(stmt)
            await session.commit()
        db_queries_total.labels(operation="set_user_model", status="success").inc()
    except Exception:
        db_queries_total.labels(operation="set_user_model", status="error").inc()
        raise
    logger.debug(f"user_id={user_id}: модель установлена в {model}")


async def get_user_memory(user_id: int) -> str | None:
    """Возвращает сохранённую память о юзере, или None если её нет."""
    try:
        async with get_session() as session:
            result = await session.execute(select(User.memory).where(User.user_id == user_id))
            value = result.scalar_one_or_none()
        db_queries_total.labels(operation="get_user_memory", status="success").inc()
        return value
    except Exception:
        db_queries_total.labels(operation="get_user_memory", status="error").inc()
        raise


async def set_user_memory(user_id: int, memory: str) -> None:
    """Сохраняет (upsert) память о юзере."""
    settings = get_settings()
    stmt = (
        sqlite_insert(User)
        .values(user_id=user_id, model=settings.default_model, memory=memory)
        .on_conflict_do_update(index_elements=[User.user_id], set_={"memory": memory})
    )
    try:
        async with get_session() as session:
            await session.execute(stmt)
            await session.commit()
        db_queries_total.labels(operation="set_user_memory", status="success").inc()
    except Exception:
        db_queries_total.labels(operation="set_user_memory", status="error").inc()
        raise
    logger.debug(f"user_id={user_id}: память обновлена ({len(memory)} символов)")


async def clear_user_memory(user_id: int) -> None:
    """Очищает память о юзере (ставит NULL)."""
    stmt = update(User).where(User.user_id == user_id).values(memory=None)
    try:
        async with get_session() as session:
            await session.execute(stmt)
            await session.commit()
        db_queries_total.labels(operation="clear_user_memory", status="success").inc()
    except Exception:
        db_queries_total.labels(operation="clear_user_memory", status="error").inc()
        raise
    logger.debug(f"user_id={user_id}: память очищена")
