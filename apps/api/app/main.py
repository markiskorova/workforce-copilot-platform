from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .db import check_database_connection

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
