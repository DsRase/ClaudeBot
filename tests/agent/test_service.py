import pytest

from src.agent.dto import IncomingMessage
from src.agent.service import ASSISTANT_USERNAME, record_message, respond


def _incoming(**overrides):
    base = dict(text="hi", user_id=1, chat_id=2, platform_msg_id=10, ts=1000, username="u")
    base.update(overrides)
    return IncomingMessage(**base)


@pytest.fixture
def settings_stub(mocker):
    s = mocker.MagicMock(
        access_user_ids=[1],
        available_models=["m1", "m2", "adaptive"],
    )
    mocker.patch("src.agent.service.get_settings", return_value=s)
    return s


@pytest.fixture
def storage_stub(mocker):
    add_msg = mocker.patch("src.agent.service.add_message", new=mocker.AsyncMock())
    get_ctx = mocker.patch("src.agent.service.get_context", new=mocker.AsyncMock(return_value=[]))
    get_model = mocker.patch("src.agent.service.get_user_model", new=mocker.AsyncMock(return_value="m1"))
    get_mem = mocker.patch("src.agent.service.get_user_memory", new=mocker.AsyncMock(return_value=None))
    return mocker.MagicMock(add=add_msg, ctx=get_ctx, model=get_model, mem=get_mem)


class _ThinkingStub:
    def __init__(self):
        self.entered = False
        self.exited = False

    async def __aenter__(self):
        self.entered = True
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.exited = True


class TestRecordMessage:
    """record_message — пишет ChatMessage в Redis-контекст."""

    @pytest.mark.asyncio
    async def test_writes_to_correct_chat(self, mocker):
        """add_message вызывается с chat_id из incoming."""
        add = mocker.patch("src.agent.service.add_message", new=mocker.AsyncMock())

        await record_message(_incoming(chat_id=42))

        assert add.await_args.args[0] == 42

    @pytest.mark.asyncio
    async def test_message_role_is_user(self, mocker):
        """Сохранённое сообщение имеет role='user'."""
        add = mocker.patch("src.agent.service.add_message", new=mocker.AsyncMock())

        await record_message(_incoming())

        msg = add.await_args.args[1]
        assert msg.role == "user"
        assert msg.text == "hi"
        assert msg.user_id == 1


class TestRespond:
    """Полный цикл respond."""

    @pytest.mark.asyncio
    async def test_no_access_sends_error(self, mocker, settings_stub, storage_stub):
        """Юзер не в access_user_ids → send_error('no_access') и выход."""
        settings_stub.access_user_ids = []
        ask = mocker.patch("src.agent.service.ask", new=mocker.AsyncMock())
        response = mocker.MagicMock(send_response=mocker.AsyncMock(), send_error=mocker.AsyncMock())

        await respond(_incoming(), response, mocker.MagicMock(), _ThinkingStub())

        response.send_error.assert_awaited_once_with("no_access")
        ask.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_happy_path_sends_response(self, mocker, settings_stub, storage_stub):
        """Успешный путь: ask → send_response → запись ассистента."""
        mocker.patch("src.agent.service.ask", new=mocker.AsyncMock(return_value="answer"))
        response = mocker.MagicMock(
            send_response=mocker.AsyncMock(return_value=999),
            send_error=mocker.AsyncMock(),
        )

        await respond(_incoming(), response, mocker.MagicMock(), _ThinkingStub())

        response.send_response.assert_awaited_once_with("answer")
        response.send_error.assert_not_awaited()
        # 2 add_message: incoming + assistant
        assert storage_stub.add.await_count == 2
        assistant_msg = storage_stub.add.await_args_list[-1].args[1]
        assert assistant_msg.role == "assistant"
        assert assistant_msg.from_username == ASSISTANT_USERNAME
        assert assistant_msg.id == 999

    @pytest.mark.asyncio
    async def test_llm_failure_sends_error(self, mocker, settings_stub, storage_stub):
        """ask упал → send_error('llm_failed'), ответ ассистента не пишется."""
        mocker.patch("src.agent.service.ask", new=mocker.AsyncMock(side_effect=RuntimeError("boom")))
        response = mocker.MagicMock(send_response=mocker.AsyncMock(), send_error=mocker.AsyncMock())

        await respond(_incoming(), response, mocker.MagicMock(), _ThinkingStub())

        response.send_error.assert_awaited_once_with("llm_failed")
        response.send_response.assert_not_awaited()
        # только incoming, ассистент не сохранён
        assert storage_stub.add.await_count == 1

    @pytest.mark.asyncio
    async def test_adaptive_calls_select_model(self, mocker, settings_stub, storage_stub):
        """Если у юзера выбрана 'adaptive' — зовётся select_model."""
        storage_stub.model.return_value = "adaptive"
        select = mocker.patch(
            "src.agent.service.select_model", new=mocker.AsyncMock(return_value="m2")
        )
        ask = mocker.patch("src.agent.service.ask", new=mocker.AsyncMock(return_value="ok"))
        response = mocker.MagicMock(send_response=mocker.AsyncMock(return_value=1), send_error=mocker.AsyncMock())

        await respond(_incoming(), response, mocker.MagicMock(), _ThinkingStub())

        select.assert_awaited_once()
        # adaptive исключается из списка кандидатов
        assert "adaptive" not in select.await_args.args[1]
        assert ask.await_args.kwargs["model"] == "m2"

    @pytest.mark.asyncio
    async def test_thinking_indicator_is_used(self, mocker, settings_stub, storage_stub):
        """thinking входит и выходит из контекста."""
        mocker.patch("src.agent.service.ask", new=mocker.AsyncMock(return_value="ok"))
        response = mocker.MagicMock(send_response=mocker.AsyncMock(return_value=1), send_error=mocker.AsyncMock())
        thinking = _ThinkingStub()

        await respond(_incoming(), response, mocker.MagicMock(), thinking)

        assert thinking.entered and thinking.exited

    @pytest.mark.asyncio
    async def test_silent_tool_names_passed_to_ask(self, mocker, settings_stub, storage_stub):
        """Имена user_memory-тул передаются в ask как silent_tool_names."""
        ask = mocker.patch("src.agent.service.ask", new=mocker.AsyncMock(return_value="ok"))
        response = mocker.MagicMock(send_response=mocker.AsyncMock(return_value=1), send_error=mocker.AsyncMock())

        await respond(_incoming(), response, mocker.MagicMock(), _ThinkingStub())

        silent = ask.await_args.kwargs["silent_tool_names"]
        assert silent == {"read_user_memory", "write_user_memory", "clear_user_memory"}

    @pytest.mark.asyncio
    async def test_user_memory_passed_to_ask(self, mocker, settings_stub, storage_stub):
        """user_memory из БД пробрасывается в ask."""
        storage_stub.mem.return_value = "MEMO"
        ask = mocker.patch("src.agent.service.ask", new=mocker.AsyncMock(return_value="ok"))
        response = mocker.MagicMock(send_response=mocker.AsyncMock(return_value=1), send_error=mocker.AsyncMock())

        await respond(_incoming(), response, mocker.MagicMock(), _ThinkingStub())

        assert ask.await_args.kwargs["user_memory"] == "MEMO"
