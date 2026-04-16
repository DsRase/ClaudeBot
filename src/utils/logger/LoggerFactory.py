import logging

class LoggerFactory:
    """Возвращает объекты logger с одинаковым конфигом."""
    _configured = False

    @classmethod
    def _configure(cls):
        """Конфиг для всех logger в проекте."""
        if cls._configured:
            return

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(name)s::%(funcName)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        cls._configured = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Создаёт экземпляр класса LoggerFactory и возвращает."""
        cls._configure()
        return logging.getLogger(name)