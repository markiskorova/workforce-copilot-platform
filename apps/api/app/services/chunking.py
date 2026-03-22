from __future__ import annotations

import re
from dataclasses import dataclass

from fastapi import HTTPException, status

from ..config import resolve_repo_relative_path

CHUNKING_VERSION = "paragraph_pack_v1"
DEFAULT_MAX_CHARS = 1000


@dataclass(slots=True)
class ChunkDraft:
    chunk_index: int
    content: str
    metadata: dict[str, object]


def load_extracted_text(extracted_text_path: str | None) -> str:
    if not extracted_text_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document version does not have extracted text to chunk.",
        )

    path = resolve_repo_relative_path(extracted_text_path)

    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extracted text file not found at {extracted_text_path}.",
        )

    return path.read_text(encoding="utf-8")


def paragraph_spans(text: str) -> list[tuple[int, int]]:
    return [
        (match.start(), match.end())
        for match in re.finditer(r"\S(?:.*?\S)?(?=\n{2,}|\Z)", text, flags=re.DOTALL)
    ]


def split_long_span(text: str, start: int, end: int, max_chars: int) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    cursor = start

    while cursor < end:
        proposed_end = min(cursor + max_chars, end)

        if proposed_end < end:
            search_start = min(cursor + max_chars // 2, proposed_end)
            whitespace_break = text.rfind(" ", search_start, proposed_end)
            if whitespace_break > cursor:
                proposed_end = whitespace_break

        if proposed_end <= cursor:
            proposed_end = min(cursor + max_chars, end)

        spans.append((cursor, proposed_end))
        cursor = proposed_end

        while cursor < end and text[cursor].isspace():
            cursor += 1

    return spans


def compact_spans(text: str, spans: list[tuple[int, int]], max_chars: int) -> list[tuple[int, int]]:
    compacted: list[tuple[int, int]] = []
    current_start: int | None = None
    current_end: int | None = None

    for span_start, span_end in spans:
        if current_start is None:
            current_start = span_start
            current_end = span_end
            continue

        proposed_length = span_end - current_start
        if proposed_length <= max_chars:
            current_end = span_end
            continue

        compacted.append((current_start, current_end or span_end))
        current_start = span_start
        current_end = span_end

    if current_start is not None and current_end is not None:
        compacted.append((current_start, current_end))

    return compacted


def build_chunk_metadata(
    *,
    content: str,
    char_start: int,
    char_end: int,
    document_id: str,
    document_version_id: str,
    document_title: str,
    filename: str,
    version_number: int,
    parser_version: str,
    normalization_version: str,
) -> dict[str, object]:
    return {
        "document_id": document_id,
        "document_version_id": document_version_id,
        "document_title": document_title,
        "filename": filename,
        "version_number": version_number,
        "char_start": char_start,
        "char_end": char_end,
        "character_count": len(content),
        "word_count": len(re.findall(r"\S+", content)),
        "parser_version": parser_version,
        "normalization_version": normalization_version,
        "chunking_version": CHUNKING_VERSION,
    }


def chunk_text(
    *,
    text: str,
    document_id: str,
    document_version_id: str,
    document_title: str,
    filename: str,
    version_number: int,
    parser_version: str,
    normalization_version: str,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> list[ChunkDraft]:
    base_spans = paragraph_spans(text)
    expanded_spans: list[tuple[int, int]] = []

    for start, end in base_spans:
        if end - start <= max_chars:
            expanded_spans.append((start, end))
            continue

        expanded_spans.extend(split_long_span(text, start, end, max_chars))

    packed_spans = compact_spans(text, expanded_spans, max_chars)

    chunk_drafts: list[ChunkDraft] = []
    for chunk_index, (start, end) in enumerate(packed_spans):
        content = text[start:end]
        metadata = build_chunk_metadata(
            content=content,
            char_start=start,
            char_end=end,
            document_id=document_id,
            document_version_id=document_version_id,
            document_title=document_title,
            filename=filename,
            version_number=version_number,
            parser_version=parser_version,
            normalization_version=normalization_version,
        )
        chunk_drafts.append(
            ChunkDraft(
                chunk_index=chunk_index,
                content=content,
                metadata=metadata,
            )
        )

    return chunk_drafts
