"""add document versions

Revision ID: 20260321_0002
Revises: 20260321_0001
Create Date: 2026-03-21 20:20:00
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260321_0002"
down_revision = "20260321_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("extracted_text_path", sa.String(length=500), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("parser_version", sa.String(length=100), nullable=False),
        sa.Column("normalization_version", sa.String(length=100), nullable=False),
        sa.Column("source_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "version_number"),
    )
    op.create_index(
        op.f("ix_document_versions_document_id"),
        "document_versions",
        ["document_id"],
        unique=False,
    )

    connection = op.get_bind()
    now = datetime.now(timezone.utc)
    document_rows = connection.execute(
        sa.text(
            """
            SELECT id, filename, content_type, storage_path, status, created_at
            FROM documents
            """
        )
    ).mappings()

    document_versions_table = sa.table(
        "document_versions",
        sa.column("id", sa.Uuid()),
        sa.column("document_id", sa.Uuid()),
        sa.column("version_number", sa.Integer()),
        sa.column("filename", sa.String()),
        sa.column("content_type", sa.String()),
        sa.column("storage_path", sa.String()),
        sa.column("extracted_text_path", sa.String()),
        sa.column("content_hash", sa.String()),
        sa.column("parser_version", sa.String()),
        sa.column("normalization_version", sa.String()),
        sa.column("source_size_bytes", sa.BigInteger()),
        sa.column("status", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )

    version_rows = []
    document_version_map: dict[str, str] = {}

    for document in document_rows:
        version_id = uuid4()
        version_rows.append(
            {
                "id": version_id,
                "document_id": document["id"],
                "version_number": 1,
                "filename": document["filename"],
                "content_type": document["content_type"],
                "storage_path": document["storage_path"] or "",
                "extracted_text_path": None,
                "content_hash": None,
                "parser_version": "legacy_v0",
                "normalization_version": "legacy_v0",
                "source_size_bytes": 0,
                "status": document["status"],
                "created_at": document["created_at"] or now,
            }
        )
        document_version_map[str(document["id"])] = str(version_id)

    if version_rows:
        op.bulk_insert(document_versions_table, version_rows)

    with op.batch_alter_table("chunks") as batch_op:
        batch_op.add_column(sa.Column("document_version_id", sa.Uuid(), nullable=True))

    for document_id, version_id in document_version_map.items():
        connection.execute(
            sa.text(
                """
                UPDATE chunks
                SET document_version_id = :version_id
                WHERE document_id = :document_id
                """
            ),
            {
                "version_id": version_id,
                "document_id": document_id,
            },
        )

    with op.batch_alter_table("chunks") as batch_op:
        batch_op.drop_constraint("chunks_document_id_chunk_index_key", type_="unique")
        batch_op.create_foreign_key(
            "fk_chunks_document_version_id_document_versions",
            "document_versions",
            ["document_version_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_unique_constraint(
            "uq_chunks_document_version_id_chunk_index",
            ["document_version_id", "chunk_index"],
        )
        batch_op.alter_column("document_version_id", nullable=False)
        batch_op.drop_column("document_id")

    op.create_index(
        op.f("ix_chunks_document_version_id"),
        "chunks",
        ["document_version_id"],
        unique=False,
    )


def downgrade() -> None:
    connection = op.get_bind()
    document_rows = connection.execute(
        sa.text(
            """
            SELECT id, document_id
            FROM document_versions
            WHERE version_number = 1
            """
        )
    ).mappings()

    with op.batch_alter_table("chunks") as batch_op:
        batch_op.add_column(sa.Column("document_id", sa.Uuid(), nullable=True))

    for row in document_rows:
        connection.execute(
            sa.text(
                """
                UPDATE chunks
                SET document_id = :document_id
                WHERE document_version_id = :document_version_id
                """
            ),
            {
                "document_id": row["document_id"],
                "document_version_id": row["id"],
            },
        )

    op.drop_index(op.f("ix_chunks_document_version_id"), table_name="chunks")

    with op.batch_alter_table("chunks") as batch_op:
        batch_op.drop_constraint(
            "uq_chunks_document_version_id_chunk_index",
            type_="unique",
        )
        batch_op.drop_constraint(
            "fk_chunks_document_version_id_document_versions",
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            None,
            "documents",
            ["document_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_unique_constraint(None, ["document_id", "chunk_index"])
        batch_op.alter_column("document_id", nullable=False)
        batch_op.drop_column("document_version_id")

    op.create_index(op.f("ix_chunks_document_id"), "chunks", ["document_id"], unique=False)
    op.drop_index(op.f("ix_document_versions_document_id"), table_name="document_versions")
    op.drop_table("document_versions")
