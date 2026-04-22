import pytest
from langchain_core.messages import AIMessage

from src.agent.llm.modelSelector import ADAPTIVE_MODEL_NAME, select_model


@pytest.fixture
def settings_stub(mocker):
    s = mocker.MagicMock(
        adaptive_selector_model="selector",
        llm_api_key="k",
        llm_base_url="http://x",
        fetch_user_agent="UA",
        default_model="default-m",
    )
    mocker.patch("src.agent.llm.modelSelector.get_settings", return_value=s)
    return s


def _llm_returning(mocker, response):
    llm = mocker.MagicMock()
    llm.ainvoke = mocker.AsyncMock(return_value=response)
    llm.bind_tools = mocker.MagicMock(return_value=llm)
    mocker.patch("src.agent.llm.modelSelector.ChatOpenAI", return_value=llm)
    return llm


class TestAdaptiveModelName:
    """Константа ADAPTIVE_MODEL_NAME."""

    def test_value(self):
        """Значение — строка 'adaptive'."""
        assert ADAPTIVE_MODEL_NAME == "adaptive"


class TestSelectModel:
    """Сценарии select_model."""

    @pytest.mark.asyncio
    async def test_returns_chosen_model_when_valid(self, mocker, settings_stub):
        """Если selector выбрал модель из available — возвращается она."""
        _llm_returning(
            mocker,
            AIMessage(content="", tool_calls=[{"name": "choose_model", "args": {"model": "gpt-5.4"}, "id": "1"}]),
        )

        result = await select_model("hello", ["gpt-5.4", "claude-opus-4.7"])

        assert result == "gpt-5.4"

    @pytest.mark.asyncio
    async def test_falls_back_when_chosen_not_in_available(self, mocker, settings_stub):
        """Если selector вернул модель не из списка — fallback на default_model."""
        _llm_returning(
            mocker,
            AIMessage(content="", tool_calls=[{"name": "choose_model", "args": {"model": "unknown"}, "id": "1"}]),
        )

        result = await select_model("hello", ["gpt-5.4"])

        assert result == "default-m"

    @pytest.mark.asyncio
    async def test_falls_back_when_no_tool_calls(self, mocker, settings_stub):
        """Если selector не выдал tool_call — fallback."""
        _llm_returning(mocker, AIMessage(content="just text"))

        result = await select_model("hello", ["gpt-5.4"])

        assert result == "default-m"

    @pytest.mark.asyncio
    async def test_falls_back_on_exception(self, mocker, settings_stub):
        """Любая ошибка LLM → fallback."""
        llm = mocker.MagicMock()
        llm.ainvoke = mocker.AsyncMock(side_effect=RuntimeError("boom"))
        llm.bind_tools = mocker.MagicMock(return_value=llm)
        mocker.patch("src.agent.llm.modelSelector.ChatOpenAI", return_value=llm)

        result = await select_model("hello", ["gpt-5.4"])

        assert result == "default-m"
