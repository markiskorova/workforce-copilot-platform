"""add index versions and entries

Revision ID: 20260321_0004
Revises: 20260321_0003
Create Date: 2026-03-21 22:05:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260321_0004"
down_revision = "20260321_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "index_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("embedding_provider", sa.String(length=100), nullable=False),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("vector_dimensions", sa.Integer(), nullable=False),
        sa.Column("chunking_version", sa.String(length=100), nullable=True),
        sa.Column("faiss_index_path", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("document_version_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("built_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_index_versions_is_active"),
        "index_versions",
        ["is_active"],
        unique=False,
    )

    op.create_table(
        "index_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("index_version_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_id", sa.Uuid(), nullable=False),
        sa.Column("vector_position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["chunks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["index_version_id"],
            ["index_versions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("index_version_id", "vector_position"),
        sa.UniqueConstraint("index_version_id", "chunk_id"),
    )
    op.create_index(
        op.f("ix_index_entries_index_version_id"),
        "index_entries",
        ["index_version_id"],
        unique=False,
    )

    with op.batch_alter_table("runs") as batch_op:
        batch_op.add_column(sa.Column("index_version_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_runs_index_version_id_index_versions",
            "index_versions",
            ["index_version_id"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("index_versions") as batch_op:
        batch_op.alter_column("is_active", server_default=None)
        batch_op.alter_column("document_version_count", server_default=None)
        batch_op.alter_column("chunk_count", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_constraint(
            "fk_runs_index_version_id_index_versions",
            type_="foreignkey",
        )
        batch_op.drop_column("index_version_id")

    op.drop_index(op.f("ix_index_entries_index_version_id"), table_name="index_entries")
    op.drop_table("index_entries")
    op.drop_index(op.f("ix_index_versions_is_active"), table_name="index_versions")
    op.drop_table("index_versions")
