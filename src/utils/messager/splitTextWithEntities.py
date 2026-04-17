from aiogram.types import MessageEntity

from src.utils.logger.LoggerFactory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def split_text_with_entities(
    text: str,
    entities: list[MessageEntity],
    max_size: int,
) -> list[tuple[str, list[MessageEntity]]]:
    """Делит (text, entities) на чанки <= max_size UTF-16 code units, стараясь не разрезать entity."""
    utf16_bytes = text.encode("utf-16-le")
    total_units = len(utf16_bytes) // 2

    sorted_entities = sorted(entities, key=lambda e: e.offset)

    chunks: list[tuple[str, list[MessageEntity]]] = []
    pos = 0

    while pos < total_units:
        end = min(pos + max_size, total_units)

        # Сжимаем end, если какая-то entity пересекает границу — двигаем её начало в следующий чанк.
        # Может потребоваться несколько проходов: после сдвига границы могла появиться другая entity, что её снова пересекает.
        while True:
            new_end = end
            for ent in sorted_entities:
                ent_start = ent.offset
                ent_end = ent.offset + ent.length
                if ent_start < new_end < ent_end and ent_start > pos:
                    new_end = ent_start
            if new_end == end:
                break
            end = new_end

        chunk_text = utf16_bytes[pos * 2:end * 2].decode("utf-16-le")

        chunk_entities: list[MessageEntity] = []
        for ent in sorted_entities:
            ent_start = ent.offset
            ent_end = ent.offset + ent.length
            if ent_end <= pos or ent_start >= end:
                continue
            new_offset = max(ent_start, pos) - pos
            new_length = min(ent_end, end) - max(ent_start, pos)
            chunk_entities.append(
                ent.model_copy(update={"offset": new_offset, "length": new_length})
            )

        logger.debug(
            f"Чанк [{pos}..{end}] UTF-16 units, entities: {len(chunk_entities)}"
        )
        chunks.append((chunk_text, chunk_entities))
        pos = end

    return chunks
