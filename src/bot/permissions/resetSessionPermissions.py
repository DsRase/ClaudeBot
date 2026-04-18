from src.bot.permissions.state import get_permission_state
from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def reset_session_permissions(user_id: int) -> int:
    """Сбрасывает все session-разрешения юзера. Возвращает количество удалённых тул."""
    cleared = get_permission_state().clear_session_permissions(user_id)
    logger.info(f"user_id={user_id}: сброшено session-разрешений: {cleared}")
    return cleared
