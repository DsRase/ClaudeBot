from .chat import router as chatRouter
from .commands import router as commandsRouter
from .permissions import router as permissionsRouter

__all__ = ["chatRouter", "commandsRouter", "permissionsRouter"]