import pytest

from src.utils.messager import get_random_message


class TestGetRandomMessage:
    """Сценарии возврата случайного сообщения из списка."""

    def test_one_list(self):
        """Проверяет, что из списка с одним элементом возвращается именно он."""
        text = "TEST"
        msg = get_random_message([text])

        assert msg == text, "вернулось значение, отличное от единственного в списке"

    def test_full_list(self):
        """Проверяет, что возвращаемое значение принадлежит переданному списку."""
        msgs = ["test1", "test2", "test3"]
        msg = get_random_message(msgs)

        assert msg in msgs, "вернулось значение, которого нет в исходном списке"

    def test_without_list(self):
        """Проверяет, что пустой список вызывает IndexError."""
        with pytest.raises(IndexError):
            get_random_message([])
