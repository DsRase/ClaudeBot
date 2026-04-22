import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.storage.sqlite import models
from src.storage.sqlite import users as users_module
from src.storage.sqlite.users import (
    clear_user_memory,
    get_user_memory,
    get_user_model,
    set_user_memory,
    set_user_model,
)


@pytest.fixture
def fake_settings(mocker):
    """Лёгкий стаб настроек: дефолт + список разрешённых моделей."""
    s = mocker.MagicMock()
    s.default_model = "claude-opus-4.6"
    s.available_models = ["claude-opus-4.6", "gpt-5.4"]
    mocker.patch("src.storage.sqlite.users.get_settings", return_value=s)
    return s


@pytest_asyncio.fixture
async def in_memory_db(mocker):
    """Создаёт изолированный in-memory sqlite engine и подменяет get_session в users.py."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    mocker.patch.object(users_module, "get_session", lambda: factory())
    yield engine
    await engine.dispose()


class TestGetUserModel:
    """Чтение модели юзера из БД."""

    @pytest.mark.asyncio
    async def test_returns_default_when_no_record(self, fake_settings, in_memory_db):
        """Если записи нет — отдаёт settings.default_model."""
        result = await get_user_model(user_id=42)
        assert result == "claude-opus-4.6", "без записи должен вернуться дефолт"

    @pytest.mark.asyncio
    async def test_returns_saved_model(self, fake_settings, in_memory_db):
        """Если запись есть — отдаёт её model."""
        await set_user_model(user_id=42, model="gpt-5.4")

        result = await get_user_model(user_id=42)
        assert result == "gpt-5.4", "должна вернуться модель, сохранённая для юзера"


class TestSetUserModel:
    """Запись модели юзера."""

    @pytest.mark.asyncio
    async def test_creates_record(self, fake_settings, in_memory_db):
        """Первый вызов set_user_model создаёт запись."""
        await set_user_model(user_id=42, model="gpt-5.4")
        assert await get_user_model(42) == "gpt-5.4"

    @pytest.mark.asyncio
    async def test_upserts_existing_record(self, fake_settings, in_memory_db):
        """Повторный вызов обновляет model для того же user_id, не дубль."""
        await set_user_model(user_id=42, model="gpt-5.4")
        await set_user_model(user_id=42, model="claude-opus-4.6")

        assert await get_user_model(42) == "claude-opus-4.6", "upsert не сработал"

    @pytest.mark.asyncio
    async def test_rejects_unknown_model(self, fake_settings, in_memory_db):
        """Модель вне available_models — ValueError, в БД не пишем."""
        with pytest.raises(ValueError):
            await set_user_model(user_id=42, model="nonexistent-model")

        # запись не должна была создаться → fallback на дефолт
        assert await get_user_model(42) == "claude-opus-4.6"


class TestEngine:
    """Smoke-тест на init_db: создаёт таблицу users."""

    @pytest.mark.asyncio
    async def test_init_db_creates_users_table(self, mocker, tmp_path):
        """init_db применяет схему, после неё можно делать select из users."""
        from sqlalchemy import select
        from src.storage.sqlite import engine as engine_module
        db_path = tmp_path / "bot.db"
        mocker.patch.object(engine_module, "get_settings", return_value=mocker.MagicMock(
            sqlite_path=str(db_path),
        ))
        engine_module.get_engine.cache_clear()
        engine_module._session_factory.cache_clear()
        try:
            await engine_module.init_db()
            async with engine_module.get_session() as session:
                # должно отработать без ошибок (таблица существует, пусть и пустая)
                result = await session.execute(select(models.User))
                assert result.all() == []
        finally:
            await engine_module.get_engine().dispose()
            engine_module.get_engine.cache_clear()
            engine_module._session_factory.cache_clear()


class TestGetUserMemory:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_record(self, fake_settings, in_memory_db):
        assert await get_user_memory(user_id=42) is None

    @pytest.mark.asyncio
    async def test_returns_saved_memory(self, fake_settings, in_memory_db):
        await set_user_memory(user_id=42, memory="любит котиков")
        assert await get_user_memory(user_id=42) == "любит котиков"


class TestSetUserMemory:
    @pytest.mark.asyncio
    async def test_creates_record(self, fake_settings, in_memory_db):
        await set_user_memory(user_id=7, memory="hello")
        assert await get_user_memory(7) == "hello"

    @pytest.mark.asyncio
    async def test_upserts_existing_record(self, fake_settings, in_memory_db):
        await set_user_memory(user_id=7, memory="v1")
        await set_user_memory(user_id=7, memory="v2")
        assert await get_user_memory(7) == "v2"

    @pytest.mark.asyncio
    async def test_preserves_user_model(self, fake_settings, in_memory_db):
        """set_user_memory не должен затирать ранее установленную модель."""
        await set_user_model(user_id=7, model="gpt-5.4")
        await set_user_memory(user_id=7, memory="note")
        assert await get_user_model(7) == "gpt-5.4"


class TestClearUserMemory:
    @pytest.mark.asyncio
    async def test_clears_existing_memory(self, fake_settings, in_memory_db):
        await set_user_memory(user_id=7, memory="note")
        await clear_user_memory(user_id=7)
        assert await get_user_memory(7) is None

    @pytest.mark.asyncio
    async def test_noop_when_no_record(self, fake_settings, in_memory_db):
        await clear_user_memory(user_id=999)
        assert await get_user_memory(999) is None
