import logging

class LoggerFactory:
    _configured = False

    @classmethod
    def _configure(cls):
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
        cls._configure()
        return logging.getLogger(name)