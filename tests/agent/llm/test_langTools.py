import pytest

from src.agent.llm import langTools


class TestSearchWebTool:
    """LangChain-обёртка search_web_tool."""

    def test_is_langchain_tool(self):
        """Имя/описание заданы, есть ainvoke."""
        assert langTools.search_web_tool.name == "search_web"
        assert langTools.search_web_tool.description
        assert hasattr(langTools.search_web_tool, "ainvoke")

    @pytest.mark.asyncio
    async def test_delegates_to_search_web(self, mocker):
        """Вызов проксируется в src.agent.tools.search_web с теми же аргументами."""
        mock_search = mocker.patch(
            "src.agent.llm.langTools.search_web", new=mocker.AsyncMock(return_value=[{"x": 1}])
        )

        result = await langTools.search_web_tool.ainvoke({"query": "q", "max_results": 5})

        mock_search.assert_awaited_once_with("q", max_results=5)
        assert result == [{"x": 1}]


class TestFetchUrlTool:
    """LangChain-обёртка fetch_url_tool."""

    def test_is_langchain_tool(self):
        """Имя/описание заданы."""
        assert langTools.fetch_url_tool.name == "fetch_url"
        assert langTools.fetch_url_tool.description

    @pytest.mark.asyncio
    async def test_delegates_to_fetch_url(self, mocker):
        """Прокси в src.agent.tools.fetch_url."""
        mock_fetch = mocker.patch(
            "src.agent.llm.langTools.fetch_url", new=mocker.AsyncMock(return_value="text")
        )

        result = await langTools.fetch_url_tool.ainvoke({"url": "http://x"})

        mock_fetch.assert_awaited_once_with("http://x")
        assert result == "text"


class TestChooseModelTool:
    """LangChain-обёртка choose_model_tool (structured output для selector-LLM)."""

    def test_is_langchain_tool(self):
        """Имя 'choose_model'."""
        assert langTools.choose_model_tool.name == "choose_model"

    @pytest.mark.asyncio
    async def test_returns_chosen_model(self, mocker):
        """Возвращает строку, переданную в model."""
        mocker.patch(
            "src.agent.llm.langTools.choose_model",
            new=mocker.AsyncMock(side_effect=lambda m: m),
        )

        result = await langTools.choose_model_tool.ainvoke({"model": "gpt-5.4"})

        assert result == "gpt-5.4"


class TestMakeChatScopedTools:
    """Сценарии фабрики make_chat_scoped_tools (chat_id в замыкании)."""

    def test_returns_one_tool(self):
        """Сейчас фабрика возвращает один тул — read_full_history."""
        tools = langTools.make_chat_scoped_tools(chat_id=42)
        assert len(tools) == 1
        assert tools[0].name == "read_full_history"

    @pytest.mark.asyncio
    async def test_captures_chat_id(self, mocker):
        """chat_id из замыкания пробрасывается в read_full_history."""
        mock_read = mocker.patch(
            "src.agent.llm.langTools.read_full_history",
            new=mocker.AsyncMock(return_value="hist"),
        )

        tool = langTools.make_chat_scoped_tools(chat_id=42)[0]
        result = await tool.ainvoke({})

        mock_read.assert_awaited_once_with(42)
        assert result == "hist"


class TestMakeUserMemoryTools:
    """Сценарии фабрики make_user_memory_tools."""

    def test_returns_three_tools(self):
        """read/write/clear user_memory."""
        tools = langTools.make_user_memory_tools(user_id=7)
        assert {t.name for t in tools} == {
            "read_user_memory",
            "write_user_memory",
            "clear_user_memory",
        }

    @pytest.mark.asyncio
    async def test_read_captures_user_id(self, mocker):
        """read_user_memory_tool вызывает get_user_memory_fn(user_id)."""
        mock_get = mocker.patch(
            "src.agent.llm.langTools.get_user_memory_fn",
            new=mocker.AsyncMock(return_value="mem"),
        )

        tools = langTools.make_user_memory_tools(user_id=7)
        read_tool = next(t for t in tools if t.name == "read_user_memory")
        result = await read_tool.ainvoke({})

        mock_get.assert_awaited_once_with(7)
        assert result == "mem"

    @pytest.mark.asyncio
    async def test_write_passes_content(self, mocker):
        """write_user_memory_tool пробрасывает content."""
        mock_set = mocker.patch(
            "src.agent.llm.langTools.set_user_memory_fn",
            new=mocker.AsyncMock(return_value="ok"),
        )

        tools = langTools.make_user_memory_tools(user_id=7)
        write_tool = next(t for t in tools if t.name == "write_user_memory")
        result = await write_tool.ainvoke({"content": "data"})

        mock_set.assert_awaited_once_with(7, "data")
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_clear_calls_clear_fn(self, mocker):
        """clear_user_memory_tool вызывает clear_user_memory_fn(user_id)."""
        mock_clear = mocker.patch(
            "src.agent.llm.langTools.clear_user_memory_fn",
            new=mocker.AsyncMock(return_value="ok"),
        )

        tools = langTools.make_user_memory_tools(user_id=7)
        clear_tool = next(t for t in tools if t.name == "clear_user_memory")
        await clear_tool.ainvoke({})

        mock_clear.assert_awaited_once_with(7)
