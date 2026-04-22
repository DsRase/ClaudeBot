import pytest

from src.agent.tools.adaptive.chooseModel import choose_model


class TestChooseModel:
    """choose_model — пассивный structured-output тул."""

    @pytest.mark.asyncio
    async def test_returns_passed_model(self):
        """Возвращает переданную строку как есть."""
        assert await choose_model("gpt-5.4") == "gpt-5.4"

    @pytest.mark.asyncio
    async def test_empty_string(self):
        """Пустая строка — возвращается как есть."""
        assert await choose_model("") == ""
