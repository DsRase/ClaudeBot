import pytest

from src.agent.agent import ask
from src.config.settings import Settings
from src.storage.schemas import ChatMessage


@pytest.fixture
def history():
    return [
        ChatMessage(role="user", id=10, ts=1000, text="привет", user_id=1),
    ]


class TestAsk:
    """Сценарии вызова функции ask."""

    @pytest.mark.asyncio
    async def test_returns_llm_response(self, mocker, monkeypatch, history):
        """Проверяет, что ask возвращает content из ответа модели."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")

        mock_llm = mocker.patch("src.agent.agent.ChatOpenAI").return_value
        mock_llm.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="ответ"))

        result = await ask(history)

        mock_llm.ainvoke.assert_awaited_once(), "ainvoke должен быть вызван ровно один раз"
        assert result == "ответ", "ask вернул не тот content, что ожидался"

    @pytest.mark.asyncio
    async def test_uses_default_model(self, mocker, monkeypatch, history):
        """Проверяет, что выбирается default_model из настроек."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")

        mock_cls = mocker.patch("src.agent.agent.ChatOpenAI")
        mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

        await ask(history)

        _, kwargs = mock_cls.call_args
        assert kwargs["model"] == Settings.model_fields["default_model"].default, \
            "выбрана не default_model из настроек"

    @pytest.mark.asyncio
    async def test_passes_base_url_and_api_key(self, mocker, monkeypatch, history):
        """В ChatOpenAI пробрасываются base_url и api_key из настроек."""
        from src.config import get_settings
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "secret")
        get_settings.cache_clear()

        mock_cls = mocker.patch("src.agent.agent.ChatOpenAI")
        mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

        await ask(history)

        _, kwargs = mock_cls.call_args
        assert kwargs["api_key"] == "secret", "api_key не пробросился из настроек"
        assert kwargs["base_url"] == Settings.model_fields["llm_base_url"].default, \
            "base_url не пробросился из настроек"

    @pytest.mark.asyncio
    async def test_user_metadata_in_jsonl_dump(self, mocker, monkeypatch):
        """Проверяет, что метаданные юзера попадают в JSONL-дамп для LLM (включая from_username/fname/lname)."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")

        history = [ChatMessage(
            role="user", id=10, ts=1, text="привет", user_id=1,
            from_username="vasya", fname="Вася", lname="Пупкин",
        )]
        mock_cls = mocker.patch("src.agent.agent.ChatOpenAI")
        mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

        await ask(history)

        sent = mock_cls.return_value.ainvoke.await_args[0][0][-1].content
        assert '"from_username": "vasya"' in sent, f"from_username не в JSONL: {sent!r}"
        assert '"fname": "Вася"' in sent, f"fname не в JSONL: {sent!r}"
        assert '"lname": "Пупкин"' in sent, f"lname не в JSONL: {sent!r}"
        assert '"text": "привет"' in sent, f"text не в JSONL: {sent!r}"

    @pytest.mark.asyncio
    async def test_reply_fields_in_jsonl_dump(self, mocker, monkeypatch):
        """Проверяет, что to_username и reply_id попадают в JSONL-дамп."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")

        history = [ChatMessage(
            role="user", id=10, ts=1, text="ну ок", user_id=1,
            from_username="vasya", to_username="petya", reply_id=99,
        )]
        mock_cls = mocker.patch("src.agent.agent.ChatOpenAI")
        mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

        await ask(history)

        sent = mock_cls.return_value.ainvoke.await_args[0][0][-1].content
        assert '"to_username": "petya"' in sent, f"to_username не в JSONL: {sent!r}"
        assert '"reply_id": 99' in sent, f"reply_id не в JSONL: {sent!r}"

    @pytest.mark.asyncio
    async def test_user_id_not_dumped_to_llm(self, mocker, monkeypatch):
        """user_id — внутреннее поле, в LLM не уходит."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")

        history = [ChatMessage(
            role="user", id=10, ts=1, text="привет", user_id=999888,
        )]
        mock_cls = mocker.patch("src.agent.agent.ChatOpenAI")
        mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

        await ask(history)

        sent = mock_cls.return_value.ainvoke.await_args[0][0][-1].content
        assert "999888" not in sent, f"user_id просочился в дамп для LLM: {sent!r}"
        assert "user_id" not in sent, f"ключ user_id попал в дамп для LLM: {sent!r}"

    @pytest.mark.asyncio
    async def test_history_collapsed_into_single_human_message(self, mocker, monkeypatch):
        """Проверяет, что вся история сворачивается в один HumanMessage без отдельных AIMessage."""
        from langchain_core.messages import HumanMessage, SystemMessage
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")

        history = [
            ChatMessage(role="user", id=1, ts=1, text="один", from_username="vasya", user_id=1),
            ChatMessage(role="assistant", id=2, ts=2, text="ответ1", from_username="Пипиндр"),
            ChatMessage(role="user", id=3, ts=3, text="два", from_username="petya", user_id=2),
        ]
        mock_cls = mocker.patch("src.agent.agent.ChatOpenAI")
        mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

        await ask(history)

        sent = mock_cls.return_value.ainvoke.await_args[0][0]
        assert len(sent) == 2, f"в LLM ушло {len(sent)} сообщений, ожидалось ровно 2 (system + human)"
        assert isinstance(sent[0], SystemMessage), "первое сообщение должно быть SystemMessage"
        assert isinstance(sent[1], HumanMessage), "второе сообщение должно быть HumanMessage"

    @pytest.mark.asyncio
    async def test_trigger_separated_from_history(self, mocker, monkeypatch):
        """Проверяет, что последнее сообщение явно отделено маркером 'Message to reply to NOW'."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")

        history = [
            ChatMessage(role="user", id=1, ts=1, text="старое", from_username="vasya", user_id=1),
            ChatMessage(role="user", id=2, ts=3, text="новое", from_username="petya", user_id=2),
        ]
        mock_cls = mocker.patch("src.agent.agent.ChatOpenAI")
        mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

        await ask(history)

        content = mock_cls.return_value.ainvoke.await_args[0][0][1].content
        marker_pos = content.find("Message to reply to NOW")
        assert marker_pos != -1, "триггер не отделён маркером 'Message to reply to NOW'"
        assert content.find("новое") > marker_pos, "триггерное сообщение оказалось не в секции триггера"
        assert content.find("старое") < marker_pos, "контекстное сообщение попало в секцию триггера"

    @pytest.mark.asyncio
    async def test_assistant_role_marked_in_history(self, mocker, monkeypatch):
        """Ответ ассистента в JSONL-дампе помечен role=assistant и from_username=Пипиндр."""
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")

        history = [
            ChatMessage(
                role="assistant", id=1, ts=1, text="мой ответ",
                from_username="Пипиндр", to_username="vasya", reply_id=100,
            ),
            ChatMessage(role="user", id=2, ts=2, text="новое", from_username="petya", user_id=2),
        ]
        mock_cls = mocker.patch("src.agent.agent.ChatOpenAI")
        mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=mocker.MagicMock(content="x"))

        await ask(history)

        content = mock_cls.return_value.ainvoke.await_args[0][0][1].content
        assert '"role": "assistant"' in content, f"role ассистента не в дампе: {content!r}"
        assert '"from_username": "Пипиндр"' in content, f"from_username ассистента не в дампе: {content!r}"
        assert '"to_username": "vasya"' in content, f"to_username не в дампе: {content!r}"


def _ai_message(content="", tool_calls=None):
    """Хелпер: фейковый AIMessage с указанным content и tool_calls."""
    from langchain_core.messages import AIMessage
    return AIMessage(content=content, tool_calls=tool_calls or [])


class TestAskToolLoop:
    """Сценарии tool-calling цикла внутри ask."""

    @pytest.fixture(autouse=True)
    def _env(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_TOKEN", "t")
        monkeypatch.setenv("LLM_API_KEY", "k")

    @pytest.mark.asyncio
    async def test_tool_executed_when_allowed(self, mocker, history):
        """Allow → тула вызывается, результат уходит в LLM, финальный текст возвращается."""
        mock_cls = mocker.patch("src.agent.agent.ChatOpenAI")
        bound = mock_cls.return_value.bind_tools.return_value
        bound.ainvoke = mocker.AsyncMock(side_effect=[
            _ai_message(tool_calls=[{"name": "search_web", "args": {"query": "rust"}, "id": "t1"}]),
            _ai_message(content="готово"),
        ])
        permission_requester = mocker.AsyncMock(return_value=True)
        tool = mocker.MagicMock()
        tool.name = "search_web"
        tool.ainvoke = mocker.AsyncMock(return_value=[{"title": "T"}])

        result = await ask(history, permission_requester=permission_requester, extra_tools=[tool])

        assert result == "готово"
        permission_requester.assert_awaited_once()
        tool.ainvoke.assert_awaited_once_with({"query": "rust"})
        assert bound.ainvoke.await_count == 2, "после tool-результата нужен второй вызов LLM"

    @pytest.mark.asyncio
    async def test_denied_sends_denial_to_llm(self, mocker, history):
        """Deny → тула не вызывается, в LLM уходит ToolMessage с отказом."""
        from langchain_core.messages import ToolMessage
        mock_cls = mocker.patch("src.agent.agent.ChatOpenAI")
        bound = mock_cls.return_value.bind_tools.return_value
        bound.ainvoke = mocker.AsyncMock(side_effect=[
            _ai_message(tool_calls=[{"name": "search_web", "args": {"query": "x"}, "id": "t1"}]),
            _ai_message(content="ну ладно"),
        ])
        permission_requester = mocker.AsyncMock(return_value=False)
        tool = mocker.MagicMock()
        tool.name = "search_web"
        tool.ainvoke = mocker.AsyncMock()

        result = await ask(history, permission_requester=permission_requester, extra_tools=[tool])

        tool.ainvoke.assert_not_awaited(), "при отказе тула не должна вызываться"
        second_call_messages = bound.ainvoke.await_args_list[1].args[0]
        tool_msgs = [m for m in second_call_messages if isinstance(m, ToolMessage)]
        assert len(tool_msgs) == 1 and "denied" in tool_msgs[0].content.lower(), \
            f"в LLM не ушёл ToolMessage с отказом: {tool_msgs}"
        assert result == "ну ладно"

    @pytest.mark.asyncio
    async def test_tool_error_propagates_as_message(self, mocker, history):
        """Если тула падает — её исключение оборачивается в ToolMessage с текстом ошибки."""
        from langchain_core.messages import ToolMessage
        mock_cls = mocker.patch("src.agent.agent.ChatOpenAI")
        bound = mock_cls.return_value.bind_tools.return_value
        bound.ainvoke = mocker.AsyncMock(side_effect=[
            _ai_message(tool_calls=[{"name": "search_web", "args": {}, "id": "t1"}]),
            _ai_message(content="ошибочка"),
        ])
        permission_requester = mocker.AsyncMock(return_value=True)
        tool = mocker.MagicMock()
        tool.name = "search_web"
        tool.ainvoke = mocker.AsyncMock(side_effect=RuntimeError("bang"))

        await ask(history, permission_requester=permission_requester, extra_tools=[tool])

        second_call_messages = bound.ainvoke.await_args_list[1].args[0]
        tool_msgs = [m for m in second_call_messages if isinstance(m, ToolMessage)]
        assert tool_msgs and "bang" in tool_msgs[0].content, \
            f"ошибка тулы не пробросилась в LLM как ToolMessage: {tool_msgs}"

    @pytest.mark.asyncio
    async def test_no_tools_bound_when_no_permission_requester(self, mocker, history):
        """Без permission_requester тулы не биндятся в LLM (модель не знает о них)."""
        mock_cls = mocker.patch("src.agent.agent.ChatOpenAI")
        mock_cls.return_value.ainvoke = mocker.AsyncMock(return_value=_ai_message(content="ок"))

        await ask(history)

        mock_cls.return_value.bind_tools.assert_not_called(), \
            "bind_tools не должен вызываться без permission_requester"

    @pytest.mark.asyncio
    async def test_iteration_cap_triggers_final_unbound_call(self, mocker, history, monkeypatch):
        """При cap'е делаем добавочный вызов LLM без тул, чтобы получить текстовый итог."""
        monkeypatch.setattr("src.agent.agent.get_settings", lambda: type("S", (), {
            "default_model": "m1",
            "llm_api_key": "k", "llm_base_url": "http://x",
            "max_tokens": 100,
            "fetch_user_agent": "ua",
            "agent_max_iterations": 3,
        })())
        mock_cls = mocker.patch("src.agent.agent.ChatOpenAI")
        unbound = mock_cls.return_value
        bound = unbound.bind_tools.return_value
        bound.ainvoke = mocker.AsyncMock(return_value=_ai_message(
            content="пытаюсь",
            tool_calls=[{"name": "search_web", "args": {}, "id": "t"}],
        ))
        unbound.ainvoke = mocker.AsyncMock(return_value=_ai_message(content="итог по найденному"))
        permission_requester = mocker.AsyncMock(return_value=True)
        tool = mocker.MagicMock()
        tool.name = "search_web"
        tool.ainvoke = mocker.AsyncMock(return_value="x")

        result = await ask(history, permission_requester=permission_requester, extra_tools=[tool])

        assert bound.ainvoke.await_count == 3, "должно быть ровно agent_max_iterations вызовов LLM с тулами"
        unbound.ainvoke.assert_awaited_once(), "после cap'а нужен финальный вызов БЕЗ тул"
        assert result == "итог по найденному", "при cap'е возвращается текст из финального вызова без тул"

    @pytest.mark.asyncio
    async def test_cap_final_call_sees_tool_results(self, mocker, history, monkeypatch):
        """Финальный fallback-вызов получает на вход messages со всеми ToolMessage из предыдущих итераций."""
        from langchain_core.messages import ToolMessage
        monkeypatch.setattr("src.agent.agent.get_settings", lambda: type("S", (), {
            "default_model": "m1",
            "llm_api_key": "k", "llm_base_url": "http://x",
            "max_tokens": 100,
            "fetch_user_agent": "ua",
            "agent_max_iterations": 2,
        })())
        mock_cls = mocker.patch("src.agent.agent.ChatOpenAI")
        unbound = mock_cls.return_value
        bound = unbound.bind_tools.return_value
        bound.ainvoke = mocker.AsyncMock(return_value=_ai_message(
            tool_calls=[{"name": "search_web", "args": {}, "id": "t"}],
        ))
        unbound.ainvoke = mocker.AsyncMock(return_value=_ai_message(content="ну вот"))
        permission_requester = mocker.AsyncMock(return_value=True)
        tool = mocker.MagicMock()
        tool.name = "search_web"
        tool.ainvoke = mocker.AsyncMock(return_value="результат поиска")

        await ask(history, permission_requester=permission_requester, extra_tools=[tool])

        final_messages = unbound.ainvoke.await_args.args[0]
        tool_results = [m for m in final_messages if isinstance(m, ToolMessage)]
        assert len(tool_results) == 2, \
            f"финальный вызов должен видеть оба ToolMessage из 2 итераций, увидел: {len(tool_results)}"

    @pytest.mark.asyncio
    async def test_permission_requester_gets_user_friendly_description(self, mocker, history):
        """В permission_requester передаётся русское описание из AgentMessages.tool_descriptions_for_user."""
        from src.config import AgentMessages
        mock_cls = mocker.patch("src.agent.agent.ChatOpenAI")
        bound = mock_cls.return_value.bind_tools.return_value
        bound.ainvoke = mocker.AsyncMock(side_effect=[
            _ai_message(tool_calls=[{"name": "search_web", "args": {}, "id": "t1"}]),
            _ai_message(content="ок"),
        ])
        permission_requester = mocker.AsyncMock(return_value=False)

        await ask(history, permission_requester=permission_requester)

        called_with_name, called_with_desc = permission_requester.await_args.args
        assert called_with_name == "search_web"
        assert called_with_desc == AgentMessages.tool_descriptions_for_user["search_web"], \
            "permission_requester получил неожиданное описание тулы"
