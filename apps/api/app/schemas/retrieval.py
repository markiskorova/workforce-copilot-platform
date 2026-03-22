from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class BuildIndexRequest(BaseModel):
    name: str | None = None
    activate: bool = True
    document_version_ids: list[UUID] | None = None


class RetrievalQueryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=25)
