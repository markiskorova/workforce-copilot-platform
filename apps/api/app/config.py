from __future__ import annotations

import os
from pathlib import Path


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_uploads_root() -> Path:
    configured_root = os.getenv("LOCAL_FILE_STORAGE_ROOT")

    if configured_root:
        return Path(configured_root).expanduser().resolve()

    return get_repo_root() / "data" / "uploads"


def get_indexes_root() -> Path:
    configured_root = os.getenv("LOCAL_INDEX_STORAGE_ROOT")

    if configured_root:
        return Path(configured_root).expanduser().resolve()

    return get_repo_root() / "data" / "indexes"


def resolve_repo_relative_path(relative_path: str) -> Path:
    return (get_repo_root() / relative_path).resolve()


def to_repo_relative_path(path: Path) -> str:
    return path.resolve().relative_to(get_repo_root()).as_posix()
