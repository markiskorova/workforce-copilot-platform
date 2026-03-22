from __future__ import annotations

import os

import psycopg


def get_database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql://workforce:workforce@localhost:5432/workforce_copilot",
    )


def check_database_connection() -> None:
    with psycopg.connect(get_database_url(), connect_timeout=3) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
