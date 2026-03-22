from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status

from ..config import get_repo_root, get_uploads_root

SUPPORTED_SUFFIXES: dict[str, str] = {
    ".txt": "plain_text_v1",
    ".md": "markdown_text_v1",
    ".markdown": "markdown_text_v1",
}

SUPPORTED_CONTENT_TYPES = {
    "text/markdown",
    "text/plain",
    "text/x-markdown",
}

NORMALIZATION_VERSION = "normalize_text_v1"


@dataclass(slots=True)
class ParsedUpload:
    original_filename: str
    sanitized_filename: str
    content_type: str
    raw_bytes: bytes
    normalized_text: str
    content_hash: str
    size_bytes: int
    parser_version: str
    normalization_version: str


def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).name).strip("-")
    return cleaned or "upload.txt"


def derive_document_title(filename: str) -> str:
    return Path(filename).stem.replace("_", " ").replace("-", " ").strip() or "Untitled document"


def normalize_text(raw_text: str) -> str:
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = "\n".join(line.rstrip() for line in normalized.split("\n"))
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def to_repo_relative_path(path: Path) -> str:
    repo_root = get_repo_root()
    return path.resolve().relative_to(repo_root).as_posix()


async def parse_upload(file: UploadFile) -> ParsedUpload:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must include a filename.",
        )

    suffix = Path(file.filename).suffix.lower()
    content_type = (file.content_type or "").lower()

    if suffix not in SUPPORTED_SUFFIXES and content_type not in SUPPORTED_CONTENT_TYPES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Supported extensions: {supported}",
        )

    parser_version = SUPPORTED_SUFFIXES.get(suffix, "plain_text_v1")
    raw_bytes = await file.read()

    if not raw_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    raw_text = raw_bytes.decode("utf-8-sig", errors="replace")
    normalized_text = normalize_text(raw_text)

    if not normalized_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file does not contain usable text after normalization.",
        )

    return ParsedUpload(
        original_filename=file.filename,
        sanitized_filename=sanitize_filename(file.filename),
        content_type=content_type or "text/plain",
        raw_bytes=raw_bytes,
        normalized_text=normalized_text,
        content_hash=hashlib.sha256(raw_bytes).hexdigest(),
        size_bytes=len(raw_bytes),
        parser_version=parser_version,
        normalization_version=NORMALIZATION_VERSION,
    )


def save_parsed_upload(
    *,
    document_id: UUID,
    version_number: int,
    parsed_upload: ParsedUpload,
) -> tuple[str, str]:
    version_dir = get_uploads_root() / str(document_id) / f"v{version_number:04d}"
    version_dir.mkdir(parents=True, exist_ok=True)

    source_path = version_dir / parsed_upload.sanitized_filename
    extracted_text_path = version_dir / "extracted.txt"

    source_path.write_bytes(parsed_upload.raw_bytes)
    extracted_text_path.write_text(parsed_upload.normalized_text, encoding="utf-8")

    return (
        to_repo_relative_path(source_path),
        to_repo_relative_path(extracted_text_path),
    )
