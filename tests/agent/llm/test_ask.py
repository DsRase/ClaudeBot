import pytest
from langchain_core.messages import AIMessage, ToolMessage

from src.agent.llm import ask as ask_module
from src.agent.llm.ask import _extract_text, _render_history, ask
from src.storage.schemas import ChatMessage


class TestRenderHistory:
    """Сборка текстового представления истории для LLM-промпта."""

    def test_empty_history_returns_placeholder(self):
        """Пустой контекст → placeholder про отсутствие сообщения."""
        assert "no message" in _render_history([])

    def test_single_message_is_trigger_only(self):
        """Одно сообщение — только trigger-блок, без context-блока."""
        msg = ChatMessage(role="user", id=1, ts=1000, text="hi")
        rendered = _render_history([msg])
        assert "Message to reply to NOW" in rendered
        assert "Chat history" not in rendered

    def test_multiple_messages_split_context_and_trigger(self):
        """Несколько сообщений — последнее это trigger, остальные — context."""
        msgs = [
            ChatMessage(role="user", id=1, ts=1000, text="first"),
            ChatMessage(role="user", id=2, ts=2000, text="trigger"),
        ]
        rendered = _render_history(msgs)
        assert "Chat history" in rendered
        assert rendered.index("first") < rendered.index("trigger")


class TestExtractText:
    """Извлечение текста из ответа LLM."""

    def test_string_content(self):
        """str → возвращается как есть."""
        assert _extract_text("hi") == "hi"

    def test_list_of_text_blocks(self):
        """list блоков → склеиваются только те, где type=='text'."""
        content = [
            {"type": "text", "text": "a"},
            {"type": "image", "url": "x"},
            {"type": "text", "text": "b"},
        ]
        assert _extract_text(content) == "ab"

    def test_unknown_type_returns_empty(self):
        """Неизвестный тип content → пустая строка."""
        assert _extract_text(123) == ""


@pytest.fixture
def settings_stub(mocker):
    s = mocker.MagicMock(
        llm_api_key="k",
        llm_base_url="http://x",
        max_tokens=100,
        fetch_user_agent="UA",
        agent_max_iterations=5,
    )
    mocker.patch("src.agent.llm.ask.get_settings", return_value=s)
    return s


def _make_llm(mocker, responses):
    """Возвращает мок ChatOpenAI. responses — список AIMessage по одному на ainvoke."""
    llm = mocker.MagicMock()
    llm.ainvoke = mocker.AsyncMock(side_effect=list(responses))
    llm.bind_tools = mocker.MagicMock(return_value=llm)
    mocker.patch("src.agent.llm.ask.ChatOpenAI", return_value=llm)
    return llm


class TestAsk:
    """Сценарии ask() — основной агентский цикл."""

    @pytest.mark.asyncio
    async def test_returns_text_when_no_tool_calls(self, mocker, settings_stub):
        """Без tool_calls сразу возвращается текст."""
        _make_llm(mocker, [AIMessage(content="answer")])

        result = await ask(
            history=[ChatMessage(role="user", id=1, ts=1000, text="hi")],
            model="m",
            tools=[],
        )

        assert result == "answer"

    @pytest.mark.asyncio
    async def test_strips_think_tags(self, mocker, settings_stub):
        """<think>...</think> вычищается."""
        _make_llm(mocker, [AIMessage(content="<think>plan</think>real")])

        result = await ask(
            history=[ChatMessage(role="user", id=1, ts=1000, text="hi")],
            model="m",
            tools=[],
        )

        assert result == "real"

    @pytest.mark.asyncio
    async def test_tool_call_loop_executes_allowed_tool(self, mocker, settings_stub):
        """Если LLM просит тулу и юзер разрешил — тула вызывается, цикл продолжается."""
        first = AIMessage(
            content="",
            tool_calls=[{"name": "search_web", "args": {"q": "x"}, "id": "c1"}],
        )
        second = AIMessage(content="final")
        _make_llm(mocker, [first, second])

        tool = mocker.MagicMock()
        tool.name = "search_web"
        tool.ainvoke = mocker.AsyncMock(return_value="results")

        permissions = mocker.MagicMock()
        permissions.request = mocker.AsyncMock(return_value=True)

        result = await ask(
            history=[ChatMessage(role="user", id=1, ts=1000, text="hi")],
            model="m",
            tools=[tool],
            permission_requester=permissions,
        )

        permissions.request.assert_awaited_once()
        tool.ainvoke.assert_awaited_once_with({"q": "x"})
        assert result == "final"

    @pytest.mark.asyncio
    async def test_denied_tool_returns_denial_message(self, mocker, settings_stub):
        """Если юзер отказал — тула не вызывается, в LLM уходит ToolMessage с denial."""
        first = AIMessage(
            content="",
            tool_calls=[{"name": "search_web", "args": {}, "id": "c1"}],
        )
        second = AIMessage(content="ok")
        _make_llm(mocker, [first, second])

        tool = mocker.MagicMock()
        tool.name = "search_web"
        tool.ainvoke = mocker.AsyncMock()

        permissions = mocker.MagicMock()
        permissions.request = mocker.AsyncMock(return_value=False)

        await ask(
            history=[ChatMessage(role="user", id=1, ts=1000, text="hi")],
            model="m",
            tools=[tool],
            permission_requester=permissions,
        )

        tool.ainvoke.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_silent_tool_skips_permission(self, mocker, settings_stub):
        """Для тулы из silent_tool_names permission НЕ запрашивается."""
        first = AIMessage(
            content="",
            tool_calls=[{"name": "read_user_memory", "args": {}, "id": "c1"}],
        )
        second = AIMessage(content="ok")
        _make_llm(mocker, [first, second])

        tool = mocker.MagicMock()
        tool.name = "read_user_memory"
        tool.ainvoke = mocker.AsyncMock(return_value="mem")

        permissions = mocker.MagicMock()
        permissions.request = mocker.AsyncMock()

        await ask(
            history=[ChatMessage(role="user", id=1, ts=1000, text="hi")],
            model="m",
            tools=[tool],
            permission_requester=permissions,
            silent_tool_names={"read_user_memory"},
        )

        permissions.request.assert_not_awaited()
        tool.ainvoke.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error_message(self, mocker, settings_stub):
        """Если LLM попросила несуществующую тулу — отдаём ToolMessage с error."""
        first = AIMessage(
            content="",
            tool_calls=[{"name": "wat", "args": {}, "id": "c1"}],
        )
        second = AIMessage(content="ok")
        _make_llm(mocker, [first, second])

        permissions = mocker.MagicMock()
        permissions.request = mocker.AsyncMock(return_value=True)

        tool = mocker.MagicMock()
        tool.name = "search_web"

        result = await ask(
            history=[ChatMessage(role="user", id=1, ts=1000, text="hi")],
            model="m",
            tools=[tool],
            permission_requester=permissions,
        )

        assert result == "ok"

    @pytest.mark.asyncio
    async def test_max_iterations_does_final_call_without_tools(self, mocker, settings_stub):
        """При достижении cap делается ещё один вызов без tool-binding для текстового ответа."""
        settings_stub.agent_max_iterations = 1
        looping = AIMessage(
            content="",
            tool_calls=[{"name": "search_web", "args": {}, "id": "c1"}],
        )
        final = AIMessage(content="forced final")
        _make_llm(mocker, [looping, final])

        tool = mocker.MagicMock()
        tool.name = "search_web"
        tool.ainvoke = mocker.AsyncMock(return_value="r")

        permissions = mocker.MagicMock()
        permissions.request = mocker.AsyncMock(return_value=True)

        result = await ask(
            history=[ChatMessage(role="user", id=1, ts=1000, text="hi")],
            model="m",
            tools=[tool],
            permission_requester=permissions,
        )

        assert result == "forced final"

    @pytest.mark.asyncio
    async def test_user_memory_appended_to_system_prompt(self, mocker, settings_stub):
        """user_memory дописывается в SystemMessage."""
        llm = _make_llm(mocker, [AIMessage(content="ok")])

        await ask(
            history=[ChatMessage(role="user", id=1, ts=1000, text="hi")],
            model="m",
            tools=[],
            user_memory="MEMO",
        )

        sent_messages = llm.ainvoke.await_args.args[0]
        system_text = sent_messages[0].content
        assert "MEMO" in system_text
