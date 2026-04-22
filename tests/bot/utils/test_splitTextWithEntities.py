from aiogram.types import MessageEntity

from src.bot.utils.splitTextWithEntities import split_text_with_entities


def _bold(offset: int, length: int) -> MessageEntity:
    return MessageEntity(type="bold", offset=offset, length=length)


class TestSplitTextWithEntities:
    """Разбивка текста с TG-entity на чанки <= max_size UTF-16 code units."""

    def test_no_split_needed(self):
        """Текст короче max_size → один чанк целиком."""
        chunks = split_text_with_entities("hello", [_bold(0, 5)], max_size=100)
        assert len(chunks) == 1
        assert chunks[0][0] == "hello"
        assert chunks[0][1][0].length == 5

    def test_simple_split(self):
        """Текст без entity делится по границе max_size."""
        chunks = split_text_with_entities("abcdefghij", [], max_size=4)
        assert [c[0] for c in chunks] == ["abcd", "efgh", "ij"]

    def test_avoids_splitting_inside_entity(self):
        """Если entity пересекает границу — она целиком уезжает в следующий чанк."""
        chunks = split_text_with_entities("abcXYZdef", [_bold(3, 3)], max_size=5)
        assert chunks[0][0] == "abc"
        assert chunks[1][0].startswith("XYZ")

    def test_entity_at_start_kept_whole(self):
        """Entity в начале (ent_start <= pos) не двигает границу — режется как обычно."""
        chunks = split_text_with_entities("XYZdef", [_bold(0, 6)], max_size=4)
        assert len(chunks) == 2
        first_ent = chunks[0][1][0]
        assert first_ent.offset == 0 and first_ent.length == 4
        second_ent = chunks[1][1][0]
        assert second_ent.offset == 0 and second_ent.length == 2

    def test_entity_offsets_relative_to_chunk(self):
        """Entity в каждом чанке должны иметь оффсет относительно начала чанка."""
        chunks = split_text_with_entities("ab cd ef", [_bold(3, 2)], max_size=5)
        for chunk_text, entities in chunks:
            for ent in entities:
                assert 0 <= ent.offset <= len(chunk_text.encode("utf-16-le")) // 2

    def test_unicode_counted_in_utf16_units(self):
        """Многобайтовые символы считаются в UTF-16 code units."""
        text = "абвгде"
        chunks = split_text_with_entities(text, [], max_size=3)
        assert chunks[0][0] == "абв"
        assert chunks[1][0] == "где"
