from aiogram.types import MessageEntity

from src.utils.messager import split_text_with_entities


def test_short_text_returns_single_chunk():
    """Проверяет, что короткий текст возвращается одним чанком без изменений."""
    text = "привет"
    entities = [MessageEntity(type="bold", offset=0, length=6)]

    result = split_text_with_entities(text, entities, max_size=100)

    assert len(result) == 1, f"короткий текст не должен делиться, получено чанков: {len(result)}"
    assert result[0][0] == text, "текст чанка не совпадает с исходным"
    assert result[0][1] == entities, "entities были изменены, хотя не должны были"


def test_long_text_split_without_entities():
    """Проверяет деление длинного текста без entities на ожидаемое число чанков."""
    text = "a" * 10
    result = split_text_with_entities(text, [], max_size=4)

    assert len(result) == 3, f"ожидалось 3 чанка (4+4+2), получено: {len(result)}"
    assert [c[0] for c in result] == ["aaaa", "aaaa", "aa"], \
        "содержимое чанков не соответствует ожидаемому делению"


def test_entity_on_boundary_moves_to_next_chunk():
    """Проверяет, что entity на границе чанка переносится целиком в следующий чанк."""
    text = "привет мой дорогой друг. Как твои дела"
    friend_start = text.index("друг")
    entities = [MessageEntity(type="bold", offset=friend_start, length=4)]

    result = split_text_with_entities(text, entities, max_size=22)

    assert "друг" not in result[0][0], "entity не должна попадать в первый чанк, а попала"
    assert "друг" in result[1][0], "entity должна была переехать во второй чанк, но её там нет"
    assert len(result[0][1]) == 0, "в первом чанке оказались лишние entities"
    chunk_text, chunk_entities = result[1]
    ent = chunk_entities[0]
    assert chunk_text[ent.offset:ent.offset + ent.length] == "друг", \
        "offset/length entity во втором чанке указывают не на 'друг'"


def test_entity_bigger_than_chunk_gets_clipped():
    """Проверяет, что entity длиннее max_size клипается по границе чанка."""
    text = "a" * 20
    entities = [MessageEntity(type="bold", offset=0, length=20)]

    result = split_text_with_entities(text, entities, max_size=8)

    expected = [(0, 8), (0, 8), (0, 4)]
    actual = [(c[1][0].offset, c[1][0].length) for c in result]
    assert actual == expected, \
        f"entity клипнута неверно: ожидалось {expected}, получено {actual}"


def test_entity_fully_in_first_chunk_preserved():
    """Проверяет, что entity полностью внутри чанка сохраняет offset и length."""
    text = "a" * 10 + "b" * 10
    entities = [MessageEntity(type="italic", offset=2, length=5)]

    result = split_text_with_entities(text, entities, max_size=10)

    first_chunk_entities = result[0][1]
    assert len(first_chunk_entities) == 1, \
        f"в первом чанке entity потеряна или дублирована, найдено: {len(first_chunk_entities)}"
    ent = first_chunk_entities[0]
    assert (ent.offset, ent.length) == (2, 5), \
        f"offset/length изменились, было (2, 5), стало ({ent.offset}, {ent.length})"
    assert len(result[1][1]) == 0, "во второй чанк просочилась entity, которой там быть не должно"


def test_emoji_offsets_in_utf16():
    """Проверяет, что offset/length считаются в UTF-16 code units (эмодзи = 2 юнита)."""
    text = "😀bold"  # эмодзи занимает 2 UTF-16 юнита
    entities = [MessageEntity(type="bold", offset=2, length=4)]

    result = split_text_with_entities(text, entities, max_size=100)

    chunk_text, chunk_entities = result[0]
    assert chunk_text == text, "текст с эмодзи был изменён, хотя должен пройти как есть"
    assert (chunk_entities[0].offset, chunk_entities[0].length) == (2, 4), \
        "offset/length для текста с эмодзи изменились, а должны были остаться прежними"
