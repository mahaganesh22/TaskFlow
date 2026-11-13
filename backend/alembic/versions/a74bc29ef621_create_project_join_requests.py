"""create project join requests

Revision ID: a74bc29ef621
Revises: f4b5ab627cd3
Create Date: 2026-11-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a74bc29ef621"
down_revision: Union[str, Sequence[str], None] = "f4b5ab627cd3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("ck_activity_type", "activity_logs", type_="check")
    op.create_check_constraint(
        "ck_activity_type",
        "activity_logs",
        "activity_type IN ('TASK_CREATED', 'TASK_STATUS_CHANGED', 'TASK_ASSIGNED', 'COMMENT_ADDED', 'MEMBER_INVITED', 'MEMBER_JOINED', 'MEMBER_REMOVED')"
    )
    op.create_table(
        "project_join_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('PENDING', 'ACCEPTED', 'REJECTED')",
            name="ck_project_join_request_status"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_join_request")
    )
    op.create_index("ix_project_join_requests_project_id", "project_join_requests", ["project_id"])
    op.create_index("ix_project_join_requests_user_id", "project_join_requests", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_project_join_requests_user_id", table_name="project_join_requests")
    op.drop_index("ix_project_join_requests_project_id", table_name="project_join_requests")
    op.drop_table("project_join_requests")
    op.drop_constraint("ck_activity_type", "activity_logs", type_="check")
    op.create_check_constraint(
        "ck_activity_type",
        "activity_logs",
        "activity_type IN ('TASK_CREATED', 'TASK_STATUS_CHANGED', 'TASK_ASSIGNED', 'COMMENT_ADDED', 'MEMBER_INVITED', 'MEMBER_REMOVED')"
    )
