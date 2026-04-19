from sqlalchemy import BigInteger, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    """Юзерские настройки. Создаётся только когда юзер реально что-то поменял."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    model: Mapped[str] = mapped_column(String, nullable=False, default="claude-opus-4.6")
    memory: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
