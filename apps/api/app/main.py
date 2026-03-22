from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, selectinload

from .db import check_database_connection, get_db_session
from .models import (
    Chunk,
    Conversation,
    Document,
    DocumentVersion,
    IndexEntry,
    IndexVersion,
    Run,
)
from .schemas.retrieval import BuildIndexRequest, RetrievalQueryRequest
from .services.chunking import CHUNKING_VERSION, chunk_text, load_extracted_text
from .services.document_ingestion import (
    derive_document_title,
    parse_upload,
    save_parsed_upload,
)
from .services.vector_indexing import (
    build_index_artifacts,
    embedding_provider_config,
    search_index,
)

app = FastAPI(
    title="Workforce Copilot API",
    version="0.1.0",
    description="Backend service for the Workforce Copilot MVP.",
)


def get_next_document_version_number(session: Session, document_id: UUID) -> int:
    current_max = session.scalar(
        select(func.max(DocumentVersion.version_number)).where(
            DocumentVersion.document_id == document_id
        )
    )
    return (current_max or 0) + 1


def get_document_or_404(session: Session, document_id: UUID) -> Document:
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} was not found.",
        )
    return document


def get_document_version_or_404(
    session: Session,
    *,
    document_id: UUID,
    document_version_id: UUID | None,
) -> DocumentVersion:
    if document_version_id is not None:
        version = session.get(DocumentVersion, document_version_id)
        if version is None or version.document_id != document_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document version {document_version_id} was not found for document {document_id}.",
            )
        return version

    version = session.scalars(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number.desc())
        .limit(1)
    ).first()

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No document versions were found for document {document_id}.",
        )

    return version


def get_active_index_or_404(session: Session) -> IndexVersion:
    index_version = session.scalars(
        select(IndexVersion)
        .where(IndexVersion.is_active.is_(True))
        .order_by(IndexVersion.built_at.desc().nullslast(), IndexVersion.created_at.desc())
        .limit(1)
    ).first()

    if index_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active index version is available. Build an index first.",
        )

    if index_version.status != "ready" or not index_version.faiss_index_path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The active index version is not ready for retrieval.",
        )

    return index_version


def serialize_document_version(version: DocumentVersion) -> dict[str, object]:
    return {
        "id": str(version.id),
        "version_number": version.version_number,
        "filename": version.filename,
        "content_type": version.content_type,
        "storage_path": version.storage_path,
        "extracted_text_path": version.extracted_text_path,
        "content_hash": version.content_hash,
        "parser_version": version.parser_version,
        "normalization_version": version.normalization_version,
        "chunking_version": version.chunking_version,
        "source_size_bytes": version.source_size_bytes,
        "chunk_count": version.chunk_count,
        "status": version.status,
        "created_at": version.created_at.isoformat(),
    }


def serialize_chunk(chunk: Chunk) -> dict[str, object]:
    return {
        "id": str(chunk.id),
        "chunk_index": chunk.chunk_index,
        "content": chunk.content,
        "metadata": chunk.chunk_metadata or {},
        "created_at": chunk.created_at.isoformat(),
    }


def serialize_index_version(index_version: IndexVersion) -> dict[str, object]:
    return {
        "id": str(index_version.id),
        "name": index_version.name,
        "embedding_provider": index_version.embedding_provider,
        "embedding_model": index_version.embedding_model,
        "vector_dimensions": index_version.vector_dimensions,
        "chunking_version": index_version.chunking_version,
        "faiss_index_path": index_version.faiss_index_path,
        "status": index_version.status,
        "is_active": index_version.is_active,
        "document_version_count": index_version.document_version_count,
        "chunk_count": index_version.chunk_count,
        "created_at": index_version.created_at.isoformat(),
        "built_at": index_version.built_at.isoformat() if index_version.built_at else None,
    }


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "workforce-copilot-api", "status": "ok"}


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"service": "workforce-copilot-api", "status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    try:
        check_database_connection()
    except Exception as exc:  # pragma: no cover - exercised through live readiness checks
        raise HTTPException(
            status_code=503,
            detail={
                "service": "workforce-copilot-api",
                "status": "not_ready",
                "database": "unavailable",
                "reason": str(exc),
            },
        ) from exc

    return {
        "service": "workforce-copilot-api",
        "status": "ready",
        "database": "ok",
    }


@app.get("/api/v1/system/status")
def system_status() -> dict[str, str]:
    database_status = "ok"

    try:
        check_database_connection()
    except Exception:
        database_status = "unavailable"

    return {
        "service": "workforce-copilot-api",
        "api": "online",
        "database": database_status,
    }


@app.post("/api/v1/system/persistence-check")
def persistence_check(session: Session = Depends(get_db_session)) -> dict[str, object]:
    timestamp = datetime.now(timezone.utc).isoformat()

    conversation = Conversation(
        user_id="local-dev",
        title=f"Persistence smoke test {timestamp}",
    )
    session.add(conversation)
    session.flush()

    run = Run(
        conversation_id=conversation.id,
        question="Can the API persist core records?",
        answer="Yes. The persistence smoke check completed successfully.",
        status="completed",
        model_provider="system",
        completed_at=datetime.now(timezone.utc),
    )
    document = Document(
        title="Persistence Smoke Test Document",
        filename="smoke-test.txt",
        content_type="text/plain",
        storage_path=f"data/uploads/smoke-tests/{conversation.id}.txt",
        status="chunked",
        uploaded_by="system",
    )
    session.add_all([run, document])
    session.flush()

    version = DocumentVersion(
        document_id=document.id,
        version_number=get_next_document_version_number(session, document.id),
        filename=document.filename,
        content_type=document.content_type,
        storage_path=document.storage_path or "",
        extracted_text_path=f"data/uploads/smoke-tests/{conversation.id}-extracted.txt",
        content_hash="system-smoke-test",
        parser_version="system",
        normalization_version="system",
        chunking_version=CHUNKING_VERSION,
        source_size_bytes=42,
        chunk_count=1,
        status="chunked",
    )
    session.add(version)
    session.flush()

    chunk = Chunk(
        document_version_id=version.id,
        chunk_index=0,
        content="This is a persistence smoke test chunk.",
        chunk_metadata={
            "source": "system",
            "created_by": "persistence-check",
            "conversation_id": str(conversation.id),
            "document_version_id": str(version.id),
            "chunking_version": CHUNKING_VERSION,
        },
    )
    session.add(chunk)
    session.commit()

    counts = {
        "conversations": session.scalar(select(func.count()).select_from(Conversation))
        or 0,
        "documents": session.scalar(select(func.count()).select_from(Document)) or 0,
        "document_versions": session.scalar(
            select(func.count()).select_from(DocumentVersion)
        )
        or 0,
        "chunks": session.scalar(select(func.count()).select_from(Chunk)) or 0,
        "index_versions": session.scalar(select(func.count()).select_from(IndexVersion))
        or 0,
        "runs": session.scalar(select(func.count()).select_from(Run)) or 0,
    }

    return {
        "status": "ok",
        "created": {
            "conversation_id": str(conversation.id),
            "document_id": str(document.id),
            "document_version_id": str(version.id),
            "chunk_id": str(chunk.id),
            "run_id": str(run.id),
        },
        "counts": counts,
    }


@app.post("/api/v1/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    document_id: UUID | None = Form(default=None),
    uploaded_by: str | None = Form(default="local-dev"),
    session: Session = Depends(get_db_session),
) -> dict[str, object]:
    parsed_upload = await parse_upload(file)

    document: Document | None
    if document_id is not None:
        document = session.get(Document, document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} was not found.",
            )
    else:
        document = Document(
            title=title or derive_document_title(parsed_upload.original_filename),
            filename=parsed_upload.original_filename,
            content_type=parsed_upload.content_type,
            storage_path="",
            status="processing",
            uploaded_by=uploaded_by,
        )
        session.add(document)
        session.flush()

    version_number = get_next_document_version_number(session, document.id)
    storage_path, extracted_text_path = save_parsed_upload(
        document_id=document.id,
        version_number=version_number,
        parsed_upload=parsed_upload,
    )

    document.title = title or document.title or derive_document_title(
        parsed_upload.original_filename
    )
    document.filename = parsed_upload.original_filename
    document.content_type = parsed_upload.content_type
    document.storage_path = storage_path
    document.status = "parsed"
    document.uploaded_by = uploaded_by

    version = DocumentVersion(
        document_id=document.id,
        version_number=version_number,
        filename=parsed_upload.original_filename,
        content_type=parsed_upload.content_type,
        storage_path=storage_path,
        extracted_text_path=extracted_text_path,
        content_hash=parsed_upload.content_hash,
        parser_version=parsed_upload.parser_version,
        normalization_version=parsed_upload.normalization_version,
        chunking_version=None,
        source_size_bytes=parsed_upload.size_bytes,
        chunk_count=0,
        status="parsed",
    )
    session.add(version)
    session.commit()
    session.refresh(version)

    return {
        "document": {
            "id": str(document.id),
            "title": document.title,
            "status": document.status,
        },
        "version": {
            "id": str(version.id),
            "version_number": version.version_number,
            "content_type": version.content_type,
            "storage_path": version.storage_path,
            "extracted_text_path": version.extracted_text_path,
            "content_hash": version.content_hash,
            "parser_version": version.parser_version,
            "normalization_version": version.normalization_version,
            "chunking_version": version.chunking_version,
            "source_size_bytes": version.source_size_bytes,
            "chunk_count": version.chunk_count,
            "status": version.status,
        },
        "text_preview": parsed_upload.normalized_text[:400],
    }


@app.post("/api/v1/documents/{document_id}/chunk")
def chunk_document_version(
    document_id: UUID,
    document_version_id: UUID | None = None,
    replace_existing: bool = False,
    session: Session = Depends(get_db_session),
) -> dict[str, object]:
    document = get_document_or_404(session, document_id)
    version = get_document_version_or_404(
        session,
        document_id=document_id,
        document_version_id=document_version_id,
    )

    existing_chunk_count = session.scalar(
        select(func.count()).select_from(Chunk).where(Chunk.document_version_id == version.id)
    ) or 0

    if existing_chunk_count and not replace_existing:
        existing_chunks = session.scalars(
            select(Chunk)
            .where(Chunk.document_version_id == version.id)
            .order_by(Chunk.chunk_index.asc())
        ).all()
        return {
            "status": "ok",
            "message": "Document version was already chunked. Returning existing chunks.",
            "document_id": str(document.id),
            "document_version": serialize_document_version(version),
            "chunk_count": len(existing_chunks),
            "chunks": [serialize_chunk(chunk) for chunk in existing_chunks],
        }

    if replace_existing and existing_chunk_count:
        session.execute(delete(Chunk).where(Chunk.document_version_id == version.id))
        session.flush()

    normalized_text = load_extracted_text(version.extracted_text_path)
    chunk_drafts = chunk_text(
        text=normalized_text,
        document_id=str(document.id),
        document_version_id=str(version.id),
        document_title=document.title,
        filename=version.filename,
        version_number=version.version_number,
        parser_version=version.parser_version,
        normalization_version=version.normalization_version,
    )

    chunks = [
        Chunk(
            document_version_id=version.id,
            chunk_index=draft.chunk_index,
            content=draft.content,
            chunk_metadata=draft.metadata,
        )
        for draft in chunk_drafts
    ]
    session.add_all(chunks)

    version.chunking_version = CHUNKING_VERSION
    version.chunk_count = len(chunks)
    version.status = "chunked"
    document.status = "chunked"

    session.commit()

    return {
        "status": "ok",
        "document_id": str(document.id),
        "document_version": serialize_document_version(version),
        "chunk_count": len(chunks),
        "chunks": [serialize_chunk(chunk) for chunk in chunks],
    }


@app.get("/api/v1/documents/{document_id}")
def get_document(document_id: UUID, session: Session = Depends(get_db_session)) -> dict[str, object]:
    document = get_document_or_404(session, document_id)

    versions = session.scalars(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number.desc())
    ).all()

    return {
        "id": str(document.id),
        "title": document.title,
        "filename": document.filename,
        "content_type": document.content_type,
        "status": document.status,
        "uploaded_by": document.uploaded_by,
        "version_count": len(versions),
        "versions": [serialize_document_version(version) for version in versions],
    }


@app.get("/api/v1/documents/{document_id}/chunks")
def get_document_chunks(
    document_id: UUID,
    document_version_id: UUID | None = None,
    session: Session = Depends(get_db_session),
) -> dict[str, object]:
    document = get_document_or_404(session, document_id)
    version = get_document_version_or_404(
        session,
        document_id=document_id,
        document_version_id=document_version_id,
    )

    chunks = session.scalars(
        select(Chunk)
        .where(Chunk.document_version_id == version.id)
        .order_by(Chunk.chunk_index.asc())
    ).all()

    return {
        "document": {
            "id": str(document.id),
            "title": document.title,
        },
        "document_version": serialize_document_version(version),
        "chunk_count": len(chunks),
        "chunks": [serialize_chunk(chunk) for chunk in chunks],
    }


@app.post("/api/v1/indexes/build", status_code=status.HTTP_201_CREATED)
def build_index(
    request: BuildIndexRequest,
    session: Session = Depends(get_db_session),
) -> dict[str, object]:
    provider_config = embedding_provider_config()

    version_query = (
        select(DocumentVersion)
        .options(selectinload(DocumentVersion.document))
        .where(DocumentVersion.chunk_count > 0)
        .where(DocumentVersion.status.in_(("chunked", "indexed")))
        .order_by(DocumentVersion.created_at.asc())
    )

    if request.document_version_ids:
        version_query = version_query.where(
            DocumentVersion.id.in_(request.document_version_ids)
        )

    document_versions = session.scalars(version_query).all()

    if not document_versions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No chunked document versions are available to index.",
        )

    version_ids = [version.id for version in document_versions]
    chunks = session.scalars(
        select(Chunk)
        .where(Chunk.document_version_id.in_(version_ids))
        .order_by(Chunk.document_version_id.asc(), Chunk.chunk_index.asc())
    ).all()

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No chunks were found for the selected document versions.",
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    chunking_versions = {version.chunking_version for version in document_versions}
    index_version = IndexVersion(
        name=request.name or f"Local index build {timestamp}",
        embedding_provider=str(provider_config["provider"]),
        embedding_model=str(provider_config["model"]),
        vector_dimensions=int(provider_config["dimensions"]),
        chunking_version=(
            chunking_versions.pop() if len(chunking_versions) == 1 else "mixed"
        ),
        status="building",
        is_active=False,
    )
    session.add(index_version)
    session.flush()

    try:
        artifacts = build_index_artifacts(
            index_version_id=str(index_version.id),
            chunk_texts=[chunk.content for chunk in chunks],
            provider=index_version.embedding_provider,
            dimensions=index_version.vector_dimensions,
        )

        session.add_all(
            [
                IndexEntry(
                    index_version_id=index_version.id,
                    chunk_id=chunk.id,
                    vector_position=position,
                )
                for position, chunk in enumerate(chunks)
            ]
        )

        if request.activate:
            session.execute(update(IndexVersion).values(is_active=False))
            index_version.is_active = True

        index_version.faiss_index_path = artifacts.faiss_index_path
        index_version.status = "ready"
        index_version.document_version_count = len(document_versions)
        index_version.chunk_count = artifacts.chunk_count
        index_version.built_at = datetime.now(timezone.utc)

        for version in document_versions:
            version.status = "indexed"
            if version.document is not None:
                version.document.status = "indexed"

        session.commit()
        session.refresh(index_version)
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build the local FAISS index: {exc}",
        ) from exc

    return {
        "status": "ok",
        "index_version": serialize_index_version(index_version),
        "indexed_document_versions": [str(version.id) for version in document_versions],
    }


@app.get("/api/v1/indexes/active")
def get_active_index(session: Session = Depends(get_db_session)) -> dict[str, object]:
    index_version = get_active_index_or_404(session)
    return {"index_version": serialize_index_version(index_version)}


@app.post("/api/v1/retrieval/query")
def retrieval_query(
    request: RetrievalQueryRequest,
    session: Session = Depends(get_db_session),
) -> dict[str, object]:
    index_version = get_active_index_or_404(session)
    positions, scores = search_index(
        relative_path=index_version.faiss_index_path or "",
        provider=index_version.embedding_provider,
        dimensions=index_version.vector_dimensions,
        query=request.query,
        top_k=request.top_k,
    )

    if not positions:
        return {
            "query": request.query,
            "index_version": serialize_index_version(index_version),
            "results": [],
        }

    entries = session.scalars(
        select(IndexEntry)
        .options(
            selectinload(IndexEntry.chunk)
            .selectinload(Chunk.document_version)
            .selectinload(DocumentVersion.document)
        )
        .where(IndexEntry.index_version_id == index_version.id)
        .where(IndexEntry.vector_position.in_(positions))
    ).all()

    entry_by_position = {entry.vector_position: entry for entry in entries}
    results = []

    for position, score in zip(positions, scores, strict=False):
        entry = entry_by_position.get(position)
        if entry is None:
            continue

        chunk = entry.chunk
        document_version = chunk.document_version
        document = document_version.document

        results.append(
            {
                "score": score,
                "chunk_id": str(chunk.id),
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "metadata": chunk.chunk_metadata or {},
                "document": {
                    "id": str(document.id),
                    "title": document.title,
                },
                "document_version": {
                    "id": str(document_version.id),
                    "version_number": document_version.version_number,
                    "filename": document_version.filename,
                },
            }
        )

    return {
        "query": request.query,
        "index_version": serialize_index_version(index_version),
        "results": results,
    }
