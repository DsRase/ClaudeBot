import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, Chat, User
from src.bot.handlers.commands import start_command, help_command, getid_command
from src.config import BotMessages


class TestBotHandlers:
    """Тестовый класс для проверки хендлеров бота"""

    @pytest.fixture
    def message(self):
        """Фикстура для мока сообщения"""
        message = MagicMock(spec=Message)
        message.chat = MagicMock(spec=Chat)
        message.chat.id = 123456
        message.from_user = MagicMock(spec=User)
        message.from_user.id = 789012
        message.answer = AsyncMock()
        return message

    @pytest.mark.asyncio
    async def test_start_command(self, message, mocker):
        """Тест команды /start"""
        mock_get_random = mocker.patch(
            'src.bot.handlers.commands.get_random_message',
            return_value="Привет! Я бот-помощник"
        )

        await start_command(message)

        mock_get_random.assert_called_once_with(BotMessages.START_MESSAGE)

        message.answer.assert_called_once_with("Привет! Я бот-помощник")

    @pytest.mark.asyncio
    async def test_help_command(self, message, mocker):
        """Тест команды /help"""
        mock_get_random = mocker.patch(
            'src.bot.handlers.commands.get_random_message',
            return_value="Я умею: /start, /help, /getid"
        )

        await help_command(message)

        mock_get_random.assert_called_once_with(BotMessages.HELP_MESSAGE)
        message.answer.assert_called_once_with("Я умею: /start, /help, /getid")

    @pytest.mark.asyncio
    async def test_getid_command(self, message):
        """Тест команды /getid"""

        await getid_command(message)

        expected_text = f"Твой ID: {message.from_user.id}"
        message.answer.assert_called_once_with(expected_text)