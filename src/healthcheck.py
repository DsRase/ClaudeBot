import requests as req
from src.utils.logger import LoggerFactory

def healthcheck():
    """Проверяет обязательный выход в интернет."""
    logger = LoggerFactory.get_logger(__name__)
    try:
        response = req.get('https://google.com/', timeout=5)
        if response.status_code == 200:
            return True
        else:
            return False
    except req.exceptions.RequestException:
        logger.error("Request провалился. Нестабильное интернет соединение.")
        return False