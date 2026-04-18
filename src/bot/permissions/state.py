import asyncio
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field

from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class PendingRequest(BaseModel):
    """Pending запрос разрешения, ожидающий клика инициатора."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    initiator_user_id: int
    initiator_username: str | None
    tool_name: str
    event: asyncio.Event = Field(default_factory=asyncio.Event)
    result: bool = False
    save_for_session: bool = False


class PermissionState:
    """In-memory состояние permission-системы. Сбрасывается при перезапуске бота."""

    def __init__(self):
        # user_id → set имён тул, разрешённых до конца сессии
        self.session_permissions: dict[int, set[str]] = {}
        # request_id → активный PendingRequest
        self.pending_requests: dict[str, PendingRequest] = {}

    def is_allowed_in_session(self, user_id: int, tool_name: str) -> bool:
        """Проверяет, разрешён ли тул для юзера до конца сессии."""
        return tool_name in self.session_permissions.get(user_id, set())

    def grant_for_session(self, user_id: int, tool_name: str) -> None:
        """Разрешает тул для юзера до конца сессии."""
        self.session_permissions.setdefault(user_id, set()).add(tool_name)
        logger.debug(f"user_id={user_id}: '{tool_name}' добавлен в session-разрешения")

    def clear_session_permissions(self, user_id: int) -> int:
        """Очищает все session-разрешения юзера. Возвращает количество удалённых тул."""
        cleared = self.session_permissions.pop(user_id, set())
        return len(cleared)

    def register_request(self, request_id: str, request: PendingRequest) -> None:
        """Регистрирует новый pending-запрос в реестре."""
        self.pending_requests[request_id] = request

    def get_request(self, request_id: str) -> PendingRequest | None:
        """Возвращает pending-запрос по id или None если такого нет."""
        return self.pending_requests.get(request_id)

    def pop_request(self, request_id: str) -> PendingRequest | None:
        """Удаляет и возвращает pending-запрос по id."""
        return self.pending_requests.pop(request_id, None)


@lru_cache
def get_permission_state() -> PermissionState:
    """Возвращает синглтон состояния permission-системы."""
    logger.info("Создание PermissionState (синглтон)")
    return PermissionState()
