from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass

import faiss
import numpy as np
from fastapi import HTTPException, status

from ..config import get_indexes_root, resolve_repo_relative_path, to_repo_relative_path

DEFAULT_EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")
DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "local-hash-embedding-v1")
DEFAULT_EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))


@dataclass(slots=True)
class IndexBuildArtifacts:
    faiss_index_path: str
    vector_dimensions: int
    chunk_count: int


def embedding_provider_config() -> dict[str, str | int]:
    return {
        "provider": DEFAULT_EMBEDDING_PROVIDER,
        "model": DEFAULT_EMBEDDING_MODEL,
        "dimensions": DEFAULT_EMBEDDING_DIMENSIONS,
    }


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", text.lower())


def local_hash_embed(text: str, dimensions: int) -> np.ndarray:
    vector = np.zeros(dimensions, dtype=np.float32)

    for token in tokenize(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign

    norm = np.linalg.norm(vector)
    if norm > 0:
        vector /= norm

    return vector


def embed_texts(texts: list[str], *, provider: str, dimensions: int) -> np.ndarray:
    if provider != "local":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Embedding provider '{provider}' is not implemented in the MVP.",
        )

    return np.vstack([local_hash_embed(text, dimensions) for text in texts]).astype(
        np.float32
    )


def build_index_artifacts(
    *,
    index_version_id: str,
    chunk_texts: list[str],
    provider: str,
    dimensions: int,
) -> IndexBuildArtifacts:
    if not chunk_texts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot build an index without chunked content.",
        )

    vectors = embed_texts(chunk_texts, provider=provider, dimensions=dimensions)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    index_dir = get_indexes_root() / index_version_id
    index_dir.mkdir(parents=True, exist_ok=True)
    index_path = index_dir / "index.faiss"
    faiss.write_index(index, str(index_path))

    return IndexBuildArtifacts(
        faiss_index_path=to_repo_relative_path(index_path),
        vector_dimensions=vectors.shape[1],
        chunk_count=vectors.shape[0],
    )


def search_index(
    *,
    relative_path: str,
    provider: str,
    dimensions: int,
    query: str,
    top_k: int,
) -> tuple[list[int], list[float]]:
    path = resolve_repo_relative_path(relative_path)

    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAISS index file not found at {relative_path}.",
        )

    index = faiss.read_index(str(path))
    query_vector = embed_texts([query], provider=provider, dimensions=dimensions)
    search_k = min(top_k, index.ntotal)

    if search_k == 0:
        return [], []

    scores, positions = index.search(query_vector, search_k)
    ranked_positions = [int(position) for position in positions[0] if position >= 0]
    ranked_scores = [float(score) for score in scores[0][: len(ranked_positions)]]

    return ranked_positions, ranked_scores
