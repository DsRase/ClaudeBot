from src.config import AgentMessages


def test_system_prompt_is_not_none():
    """Проверяет, что существует system_prompt."""
    assert isinstance(AgentMessages.system_prompt, str), "Возвращается не строка"
