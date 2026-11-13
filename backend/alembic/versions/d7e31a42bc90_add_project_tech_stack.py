"""add tech stack to projects

Revision ID: d7e31a42bc90
Revises: c91a6d4e20bf
Create Date: 2026-11-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7e31a42bc90"
down_revision: Union[str, Sequence[str], None] = "c91a6d4e20bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("tech_stack", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "tech_stack")
