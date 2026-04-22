from sqlalchemy.orm import DeclarativeBase

from src.storage.sqlite.models import Base, User


class TestBase:
    def test_is_declarative_base(self):
        assert issubclass(Base, DeclarativeBase)


class TestUser:
    def test_tablename(self):
        assert User.__tablename__ == "users"

    def test_columns_present(self):
        cols = {c.name for c in User.__table__.columns}
        assert {"id", "user_id", "model", "memory"}.issubset(cols)

    def test_user_id_unique_indexed(self):
        col = User.__table__.c.user_id
        assert col.unique is True
        assert col.index is True

    def test_memory_nullable(self):
        assert User.__table__.c.memory.nullable is True

    def test_model_not_nullable(self):
        assert User.__table__.c.model.nullable is False
