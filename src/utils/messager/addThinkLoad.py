from time import sleep

from aiogram.types import Message

from src.config import get_settings


def add_think_load(message: Message):
    settings = get_settings()
    timeout = settings.permission_request_timeout
    syms = [
        "|",
        "/",
        "—",
        "\\"
    ]
    sec = 0.1
    i = 0
    while timeout > 0:
        timeout -= sec
        try:
            if i >= len(syms):
                i = 0
            message.edit_text(message.text + " " + syms[i])
        except Exception as e: # сообщение удалилось, следовательно его нельзя отредачить
            break
        sleep(sec)