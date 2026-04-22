import inspect

from src.agent.ports import ThinkingIndicator


class TestThinkingIndicatorProtocol:
    """Контракт порта ThinkingIndicator (async context manager)."""

    def test_has_aenter(self):
        """__aenter__ — async."""
        assert hasattr(ThinkingIndicator, "__aenter__")
        assert inspect.iscoroutinefunction(ThinkingIndicator.__aenter__)

    def test_has_aexit(self):
        """__aexit__ — async."""
        assert hasattr(ThinkingIndicator, "__aexit__")
        assert inspect.iscoroutinefunction(ThinkingIndicator.__aexit__)
