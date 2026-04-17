from logging import Logger

from src.utils.logger import LoggerFactory


class TestLoggerFactory:
    """Сценарии создания логгера через фабрику."""

    def test_get_logger(self):
        """Проверяет, что LoggerFactory возвращает объект стандартного Logger."""
        logger = LoggerFactory.get_logger(__name__)
        assert isinstance(logger, Logger), f"Получаемый логгер не является таковым. {type(logger)}"
