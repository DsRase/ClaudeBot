import inspect

from src.agent.ports import ResponseChannel


class TestResponseChannelProtocol:
    """Контракт порта ResponseChannel."""

    def test_has_send_response(self):
        """send_response — async-метод."""
        assert hasattr(ResponseChannel, "send_response")
        assert inspect.iscoroutinefunction(ResponseChannel.send_response)

    def test_has_send_error(self):
        """send_error — async-метод."""
        assert hasattr(ResponseChannel, "send_error")
        assert inspect.iscoroutinefunction(ResponseChannel.send_error)

    def test_send_response_signature(self):
        """send_response(text: str)."""
        sig = inspect.signature(ResponseChannel.send_response)
        assert list(sig.parameters) == ["self", "text"]

    def test_send_error_signature(self):
        """send_error(reason: str)."""
        sig = inspect.signature(ResponseChannel.send_error)
        assert list(sig.parameters) == ["self", "reason"]
