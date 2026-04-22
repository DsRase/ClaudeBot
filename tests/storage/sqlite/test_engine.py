import pytest
from sqlalchemy import select

from src.storage.sqlite import engine as engine_module
from src.storage.sqlite import models


class TestGetEngine:
    """Создание singleton-engine."""

    def test_returns_async_engine(self, mocker, tmp_path):
        """Возвращает AsyncEngine с url, собранным из settings.sqlite_path."""
        from sqlalchemy.ext.asyncio import AsyncEngine

        db_path = tmp_path / "bot.db"
        mocker.patch.object(
            engine_module,
            "get_settings",
            return_value=mocker.MagicMock(sqlite_path=str(db_path)),
        )
        engine_module.get_engine.cache_clear()
        engine_module._session_factory.cache_clear()
        try:
            engine = engine_module.get_engine()
            assert isinstance(engine, AsyncEngine), "должен вернуться AsyncEngine"
            assert str(db_path) in str(engine.url)
        finally:
            engine_module.get_engine.cache_clear()
            engine_module._session_factory.cache_clear()

    def test_caches_engine(self, mocker, tmp_path):
        """lru_cache: повторный вызов возвращает тот же инстанс."""
        db_path = tmp_path / "bot.db"
        mocker.patch.object(
            engine_module,
            "get_settings",
            return_value=mocker.MagicMock(sqlite_path=str(db_path)),
        )
        engine_module.get_engine.cache_clear()
        engine_module._session_factory.cache_clear()
        try:
            assert engine_module.get_engine() is engine_module.get_engine()
        finally:
            engine_module.get_engine.cache_clear()
            engine_module._session_factory.cache_clear()


class TestGetSession:
    """Открытие сессии."""

    @pytest.mark.asyncio
    async def test_returns_async_session(self, mocker, tmp_path):
        """get_session() возвращает AsyncSession, юзается как async with."""
        from sqlalchemy.ext.asyncio import AsyncSession

        db_path = tmp_path / "bot.db"
        mocker.patch.object(
            engine_module,
            "get_settings",
            return_value=mocker.MagicMock(sqlite_path=str(db_path)),
        )
        engine_module.get_engine.cache_clear()
        engine_module._session_factory.cache_clear()
        try:
            await engine_module.init_db()
            session = engine_module.get_session()
            assert isinstance(session, AsyncSession)
            await session.close()
        finally:
            await engine_module.get_engine().dispose()
            engine_module.get_engine.cache_clear()
            engine_module._session_factory.cache_clear()


class TestInitDb:
    """Применение схемы."""

    @pytest.mark.asyncio
    async def test_creates_users_table(self, mocker, tmp_path):
        """init_db применяет схему, после неё users-таблица доступна."""
        db_path = tmp_path / "bot.db"
        mocker.patch.object(
            engine_module,
            "get_settings",
            return_value=mocker.MagicMock(sqlite_path=str(db_path)),
        )
        engine_module.get_engine.cache_clear()
        engine_module._session_factory.cache_clear()
        try:
            await engine_module.init_db()
            async with engine_module.get_session() as session:
                result = await session.execute(select(models.User))
                assert result.all() == [], "таблица должна существовать и быть пустой"
        finally:
            await engine_module.get_engine().dispose()
            engine_module.get_engine.cache_clear()
            engine_module._session_factory.cache_clear()

    @pytest.mark.asyncio
    async def test_creates_parent_dir(self, mocker, tmp_path):
        """get_engine() создаёт parent-директорию, если её нет."""
        db_path = tmp_path / "nested" / "deep" / "bot.db"
        mocker.patch.object(
            engine_module,
            "get_settings",
            return_value=mocker.MagicMock(sqlite_path=str(db_path)),
        )
        engine_module.get_engine.cache_clear()
        engine_module._session_factory.cache_clear()
        try:
            engine_module.get_engine()
            assert db_path.parent.is_dir(), "parent должен быть создан"
        finally:
            engine_module.get_engine.cache_clear()
            engine_module._session_factory.cache_clear()
