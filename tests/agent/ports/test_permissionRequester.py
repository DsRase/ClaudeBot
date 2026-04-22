import inspect

from src.agent.ports import PermissionRequester


class TestPermissionRequesterProtocol:
    """Контракт порта PermissionRequester."""

    def test_has_request_method(self):
        """Протокол объявляет async-метод request(tool_name, description)."""
        assert hasattr(PermissionRequester, "request")
        assert inspect.iscoroutinefunction(PermissionRequester.request)

    def test_request_signature(self):
        """request принимает tool_name: str, description: str."""
        sig = inspect.signature(PermissionRequester.request)
        params = list(sig.parameters)
        assert params == ["self", "tool_name", "description"], f"неверная сигнатура: {params}"

    def test_duck_typed_implementation_is_compatible(self):
        """Класс с совместимым методом считается реализацией Protocol (runtime duck typing)."""
        class Impl:
            async def request(self, tool_name: str, description: str) -> bool:
                return True

        impl: PermissionRequester = Impl()
        assert hasattr(impl, "request")
