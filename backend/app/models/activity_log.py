import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    __table_args__ = (
        CheckConstraint(
            """
            activity_type IN (
                'TASK_CREATED',
                'TASK_STATUS_CHANGED',
                'TASK_ASSIGNED',
                'COMMENT_ADDED',
                'MEMBER_INVITED',
                'MEMBER_JOINED',
                'MEMBER_REMOVED'
            )
            """,
            name="ck_activity_type"
        ),
        Index(
            "ix_activity_project_created",
            "project_id",
            "created_at"
        )
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )

    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    activity_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False
    )

    details: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    project = relationship("Project")
    actor = relationship("User")
    task = relationship("Task")
