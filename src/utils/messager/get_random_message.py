import random
from typing import List

from src.utils import LoggerFactory


def get_random_message(messages: List[str]) -> str:
    """Возвращает случайный элемент из messages. Если список пуст, возбуждается IndexError."""
    try:
        return random.choice(messages)
    except IndexError:
        logger = LoggerFactory.get_logger(__name__)
        logger.error("IndexError. Был передан пустой список сообщений.")
        raise IndexError("Список messages пуст.")