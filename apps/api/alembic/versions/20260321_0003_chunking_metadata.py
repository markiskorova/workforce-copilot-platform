"""add chunking metadata to document versions

Revision ID: 20260321_0003
Revises: 20260321_0002
Create Date: 2026-03-21 21:10:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260321_0003"
down_revision = "20260321_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("document_versions") as batch_op:
        batch_op.add_column(sa.Column("chunking_version", sa.String(length=100), nullable=True))
        batch_op.add_column(
            sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0")
        )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE document_versions dv
            SET chunk_count = chunk_totals.chunk_count,
                chunking_version = 'legacy_chunk_v0',
                status = CASE
                    WHEN dv.status = 'parsed' THEN 'chunked'
                    ELSE dv.status
                END
            FROM (
                SELECT document_version_id, COUNT(*) AS chunk_count
                FROM chunks
                GROUP BY document_version_id
            ) AS chunk_totals
            WHERE dv.id = chunk_totals.document_version_id
            """
        )
    )

    with op.batch_alter_table("document_versions") as batch_op:
        batch_op.alter_column("chunk_count", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("document_versions") as batch_op:
        batch_op.drop_column("chunk_count")
        batch_op.drop_column("chunking_version")
