import pytest

from src.agent.langTools import ALL_TOOLS, fetch_url_tool, search_web_tool
from src.config import AgentMessages


class TestLangTools:
    """Smoke-тесты обёрток LangChain поверх pure-функций тул."""

    def test_all_tools_registry(self):
        """ALL_TOOLS содержит обе тулы под ожидаемыми именами."""
        names = {t.name for t in ALL_TOOLS}
        assert names == {"search_web", "fetch_url"}, f"неожиданный набор тул: {names}"

    def test_descriptions_come_from_agent_messages(self):
        """Описания тул для LLM берутся из AgentMessages.tool_descriptions_for_llm."""
        assert search_web_tool.description == AgentMessages.tool_descriptions_for_llm["search_web"]
        assert fetch_url_tool.description == AgentMessages.tool_descriptions_for_llm["fetch_url"]

    @pytest.mark.asyncio
    async def test_search_wrapper_delegates(self, mocker):
        """Обёртка search_web_tool делегирует в pure-функцию с теми же аргументами."""
        spy = mocker.patch("src.agent.langTools.search_web", new=mocker.AsyncMock(return_value=[{"x": 1}]))

        result = await search_web_tool.ainvoke({"query": "python", "max_results": 3})

        spy.assert_awaited_once_with("python", max_results=3)
        assert result == [{"x": 1}]

    @pytest.mark.asyncio
    async def test_fetch_wrapper_delegates(self, mocker):
        """Обёртка fetch_url_tool делегирует в pure-функцию с тем же URL."""
        spy = mocker.patch("src.agent.langTools.fetch_url", new=mocker.AsyncMock(return_value="text"))

        result = await fetch_url_tool.ainvoke({"url": "http://example.com"})

        spy.assert_awaited_once_with("http://example.com")
        assert result == "text"
