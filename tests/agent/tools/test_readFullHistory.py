import json

import pytest

from src.agent.tools.history.readFullHistory import read_full_history
from src.storage.schemas import ChatMessage


class TestReadFullHistory:
    """Сценарии вызова read_full_history."""

    @pytest.mark.asyncio
    async def test_uses_max_stored_limit(self, mocker, monkeypatch):
        """read_full_history запрашивает context_max_stored сообщений, а не дефолтный лимит."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
        mocker.patch(
            "src.agent.tools.history.readFullHistory.get_settings"
        ).return_value.context_max_stored = 500
        mock_get_context = mocker.patch(
            "src.agent.tools.history.readFullHistory.get_context",
            new=mocker.AsyncMock(return_value=[]),
        )

        await read_full_history(chat_id=42)

        mock_get_context.assert_awaited_once_with(42, limit=500), \
            "read_full_history должен звать get_context с limit=context_max_stored"

    @pytest.mark.asyncio
    async def test_returns_jsonl(self, mocker, monkeypatch):
        """Возвращается JSONL: одно сообщение на строку, ts уже отформатирован для LLM."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
        mocker.patch(
            "src.agent.tools.history.readFullHistory.get_settings"
        ).return_value.context_max_stored = 500
        history = [
            ChatMessage(role="user", id=1, ts=1000, text="привет", from_username="vasya"),
            ChatMessage(role="assistant", id=2, ts=2000, text="ответ", from_username="Пипиндр"),
        ]
        mocker.patch(
            "src.agent.tools.history.readFullHistory.get_context",
            new=mocker.AsyncMock(return_value=history),
        )

        result = await read_full_history(chat_id=42)

        lines = result.split("\n")
        assert len(lines) == 2, f"ожидалось 2 строки JSONL, получено: {len(lines)}"
        assert json.loads(lines[0])["text"] == "привет"
        assert json.loads(lines[1])["from_username"] == "Пипиндр"

    @pytest.mark.asyncio
    async def test_empty_history_returns_empty_string(self, mocker, monkeypatch):
        """Пустая история — пустая строка."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
        mocker.patch(
            "src.agent.tools.history.readFullHistory.get_settings"
        ).return_value.context_max_stored = 500
        mocker.patch(
            "src.agent.tools.history.readFullHistory.get_context",
            new=mocker.AsyncMock(return_value=[]),
        )

        result = await read_full_history(chat_id=42)

        assert result == "", f"для пустой истории ожидалась пустая строка, получено: {result!r}"
