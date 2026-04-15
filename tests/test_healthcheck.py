from src.healthcheck import healthcheck

def test_healthcheck():
    assert healthcheck() is True, "Для работы обязательно подключение к интернету."