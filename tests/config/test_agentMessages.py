from src.config import AgentMessages


class TestAgentMessages:
    """Сценарии проверки констант для агента."""

    def test_system_prompt_is_not_none(self):
        """Проверяет, что существует system_prompt."""
        assert isinstance(AgentMessages.system_prompt, str), "system_prompt оказался не строкой"
