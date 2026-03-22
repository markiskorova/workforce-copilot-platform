from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import check_database_connection, get_db_session
from .models import Chunk, Conversation, Document, Run

app = FastAPI(
    title="Workforce Copilot API",
    version="0.1.0",
    description="Backend service for the Workforce Copilot MVP.",
)


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
        storage_path=f"local://smoke-tests/{conversation.id}.txt",
        status="processed",
        uploaded_by="system",
    )
    session.add_all([run, document])
    session.flush()

    chunk = Chunk(
        document_id=document.id,
        chunk_index=0,
        content="This is a persistence smoke test chunk.",
        chunk_metadata={
            "source": "system",
            "created_by": "persistence-check",
            "conversation_id": str(conversation.id),
        },
    )
    session.add(chunk)
    session.commit()

    counts = {
        "conversations": session.scalar(select(func.count()).select_from(Conversation))
        or 0,
        "documents": session.scalar(select(func.count()).select_from(Document)) or 0,
        "chunks": session.scalar(select(func.count()).select_from(Chunk)) or 0,
        "runs": session.scalar(select(func.count()).select_from(Run)) or 0,
    }

    return {
        "status": "ok",
        "created": {
            "conversation_id": str(conversation.id),
            "document_id": str(document.id),
            "chunk_id": str(chunk.id),
            "run_id": str(run.id),
        },
        "counts": counts,
    }
