from src.healthcheck import healthcheck

def test_healthcheck():
    """Проверяет, что healthcheck возвращает True при наличии подключения к интернету."""
    assert healthcheck() is True, "Для работы обязательно подключение к интернету."