from src.healthcheck import healthcheck


class TestHealthcheck:
    """Сценарии проверки доступности интернета."""

    def test_healthcheck(self):
        """Проверяет, что healthcheck возвращает True при наличии подключения к интернету."""
        assert healthcheck() is True, "Для работы обязательно подключение к интернету."
