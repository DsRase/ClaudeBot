from logging import Logger

from src.utils.logger import LoggerFactory

def test_get_logger():
    logger = LoggerFactory.get_logger(__name__)
    assert isinstance(logger, Logger), f"Получаемый логгер не является таковым. {type(logger)}"