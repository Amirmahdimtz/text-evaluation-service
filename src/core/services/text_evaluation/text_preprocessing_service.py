"""Lossless original-text segmentation and reversible Persian normalization."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from src.infrastructure.di.inject import inject

_CHAR_MAP = str.maketrans({"ي": "ی", "ك": "ک", "ى": "ی", "ۀ": "ه"})
_MAX_DOCUMENT_CHARS = 2_000_000


@dataclass(frozen=True)
class TextChunk:
    start_offset: int
    end_offset: int
    text: str


@dataclass(frozen=True)
class PreparedText:
    original: str
    normalized: str
    normalized_to_original: tuple[tuple[int, int], ...]
    chunks: tuple[TextChunk, ...]
    source_sha256: str

    def original_span(self, start: int, end: int) -> tuple[int, int]:
        if (type(start) is not int or type(end) is not int or start < 0
                or end <= start or end > len(self.normalized_to_original)):
            raise ValueError("TEXT_OFFSET_INVALID")
        return (self.normalized_to_original[start][0],
                self.normalized_to_original[end - 1][1])


@inject
class TextPreprocessingService:
    def prepare(self, text: str, *, chunk_char_limit: int) -> PreparedText:
        if (not isinstance(text, str) or not text.strip()
                or len(text) > _MAX_DOCUMENT_CHARS
                or type(chunk_char_limit) is not int or not 32 <= chunk_char_limit <= 100_000
                or any(ord(char) == 0 or 0xD800 <= ord(char) <= 0xDFFF for char in text)):
            raise ValueError("TEXT_INPUT_INVALID")
        try:
            encoded = text.encode("utf-8")
        except UnicodeError:
            raise ValueError("TEXT_INPUT_INVALID") from None

        normalized: list[str] = []
        offsets: list[tuple[int, int]] = []
        index = 0
        while index < len(text):
            if text[index:index + 2] == "\r\n":
                normalized.append("\n")
                offsets.append((index, index + 2))
                index += 2
                continue
            normalized.append(text[index].translate(_CHAR_MAP))
            offsets.append((index, index + 1))
            index += 1

        chunks: list[TextChunk] = []
        start = 0
        while start < len(text):
            end = min(start + chunk_char_limit, len(text))
            if end < len(text):
                portion = text[start:end]
                # Prefer paragraph/sentence/word boundaries, but never discard
                # delimiters or silently omit text to fit the model window.
                boundary = max(
                    portion.rfind("\n\n"), portion.rfind("\n"),
                    portion.rfind("؟"), portion.rfind("."), portion.rfind(" "),
                )
                if boundary >= chunk_char_limit // 2:
                    end = start + boundary + 1
            chunks.append(TextChunk(start, end, text[start:end]))
            start = end
        if "".join(chunk.text for chunk in chunks) != text:
            raise ValueError("TEXT_CHUNK_INTEGRITY")
        return PreparedText(
            original=text, normalized="".join(normalized),
            normalized_to_original=tuple(offsets), chunks=tuple(chunks),
            source_sha256=hashlib.sha256(encoded).hexdigest(),
        )
