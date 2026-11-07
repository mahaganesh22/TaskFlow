
import uuid

from datetime import datetime, timezone

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class ProjectMember(Base):

    __tablename__ = "project_members"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "project_id",
            name="uq_user_project"
        ),

        CheckConstraint(
            "role IN ('OWNER', 'MEMBER')",
            name="ck_project_member_role"
        )
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    role: Mapped[str] = mapped_column(
        String(20),
        default="MEMBER",
        nullable=False
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationship with User
    user = relationship("User")

    # Relationship with Project
    project = relationship(
        "Project",
        back_populates="memberships"
    )
