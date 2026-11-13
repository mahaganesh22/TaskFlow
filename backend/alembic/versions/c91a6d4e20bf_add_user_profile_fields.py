"""add optional profile fields to users

Revision ID: c91a6d4e20bf
Revises: a74bc29ef621
Create Date: 2026-11-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c91a6d4e20bf"
down_revision: Union[str, Sequence[str], None] = "a74bc29ef621"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("education", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("skills", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("projects", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("experience", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "experience")
    op.drop_column("users", "projects")
    op.drop_column("users", "skills")
    op.drop_column("users", "education")
