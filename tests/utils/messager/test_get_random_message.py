import pytest

from src.utils.messager import get_random_message

def test_get_random_message_one_list():
    """Проверяет, что из списка с одним элементом возвращается именно он."""
    text = "TEST"
    msg = get_random_message([text])

    assert msg == text, "Возвращает значение не из списка"

def test_get_random_message_full_list():
    """Проверяет, что возвращаемое значение принадлежит переданному списку."""
    msgs = ["test1", "test2", "test3"]
    msg = get_random_message(msgs)

    assert msg in msgs, "Возвращает значение не из списка"

def test_get_random_message_without_list():
    """Проверяет, что пустой список вызывает IndexError."""
    with pytest.raises(IndexError):
          get_random_message([])