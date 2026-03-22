from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import check_database_connection, get_db_session
from .models import Chunk, Conversation, Document, DocumentVersion, Run
from .services.document_ingestion import (
    derive_document_title,
    parse_upload,
    save_parsed_upload,
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
        status="parsed",
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
        source_size_bytes=42,
        status="parsed",
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
        source_size_bytes=parsed_upload.size_bytes,
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
            "source_size_bytes": version.source_size_bytes,
            "status": version.status,
        },
        "text_preview": parsed_upload.normalized_text[:400],
    }


@app.get("/api/v1/documents/{document_id}")
def get_document(document_id: UUID, session: Session = Depends(get_db_session)) -> dict[str, object]:
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} was not found.",
        )

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
        "versions": [
            {
                "id": str(version.id),
                "version_number": version.version_number,
                "filename": version.filename,
                "content_type": version.content_type,
                "storage_path": version.storage_path,
                "extracted_text_path": version.extracted_text_path,
                "content_hash": version.content_hash,
                "parser_version": version.parser_version,
                "normalization_version": version.normalization_version,
                "source_size_bytes": version.source_size_bytes,
                "status": version.status,
                "created_at": version.created_at.isoformat(),
            }
            for version in versions
        ],
    }
