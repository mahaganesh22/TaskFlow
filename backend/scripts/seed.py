"""Seed TaskFlow with repeatable evaluator accounts and a shared project.

Run from the backend directory with ``python -m scripts.seed``. Add ``--reset``
to remove all existing TaskFlow application records before inserting the demo
data. Reset is intentionally explicit because it is destructive.
"""

import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.core.security import hash_password
from app.database.database import SessionLocal
from app.models import (
    ActivityLog,
    Comment,
    Project,
    ProjectJoinRequest,
    ProjectMember,
    RefreshToken,
    Task,
    User,
)


DEMO_PASSWORD = "TaskFlow123!"
DEMO_USERS = (
    {"name": "Maya Chen", "email": "maya@example.com"},
    {"name": "Arjun Rao", "email": "arjun@example.com"},
)
PROJECT_NAME = "TaskFlow Collaboration Demo"


def clear_application_data(db) -> None:
    """Delete rows in foreign-key order while preserving the schema/migrations."""
    for model in (
        ProjectJoinRequest,
        Comment,
        ActivityLog,
        RefreshToken,
        Task,
        ProjectMember,
        Project,
        User,
    ):
        db.execute(delete(model))


def seed(db) -> None:
    users = {}
    for spec in DEMO_USERS:
        user = db.scalar(select(User).where(User.email == spec["email"]))
        if user is None:
            user = User(**spec, password_hash=hash_password(DEMO_PASSWORD))
            db.add(user)
            db.flush()
        else:
            user.name = spec["name"]
            user.deleted_at = None
            user.password_hash = hash_password(DEMO_PASSWORD)
        users[spec["email"]] = user

    owner = users["maya@example.com"]
    member = users["arjun@example.com"]
    project = db.scalar(
        select(Project).where(
            Project.name == PROJECT_NAME,
            Project.owner_id == owner.id,
        )
    )
    if project is None:
        project = Project(
            name=PROJECT_NAME,
            description="A shared board for exploring TaskFlow collaboration.",
            tech_stack="FastAPI, React, PostgreSQL",
            owner_id=owner.id,
        )
        db.add(project)
        db.flush()

    for user, role in ((owner, "OWNER"), (member, "MEMBER")):
        membership = db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == user.id,
            )
        )
        if membership is None:
            db.add(ProjectMember(project_id=project.id, user_id=user.id, role=role))
        else:
            membership.role = role

    examples = (
        ("Review the project brief", "Confirm the goals and milestones.", "TODO", "HIGH", owner, member),
        ("Build the dashboard layout", "Create the initial dashboard view.", "IN_PROGRESS", "MEDIUM", member, owner),
        ("Add task status filters", "Filter tasks by TODO, IN_PROGRESS, and DONE.", "TODO", "LOW", owner, member),
        ("Document the API workflow", "Describe the main collaboration endpoints.", "DONE", "MEDIUM", member, owner),
    )
    for title, description, status, priority, creator, assignee in examples:
        task = db.scalar(
            select(Task).where(Task.project_id == project.id, Task.title == title)
        )
        values = {
            "description": description,
            "status": status,
            "priority": priority,
            "created_by": creator.id,
            "assignee_id": assignee.id,
            "completed_at": (
                datetime.now(timezone.utc) - timedelta(days=1)
                if status == "DONE"
                else None
            ),
        }
        if task is None:
            task = Task(title=title, project_id=project.id, **values)
            db.add(task)
        else:
            for key, value in values.items():
                setattr(task, key, value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--reset",
        action="store_true",
        help="delete all existing application records before seeding",
    )

    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="delete all application records without inserting demo data",
    )

    args = parser.parse_args()

    with SessionLocal.begin() as db:
        if args.reset or args.clean_only:
            clear_application_data(db)

        if not args.clean_only:
            seed(db)

    if args.clean_only:
        print("Database cleaned successfully.")
        return

    print("Seeded 2 users, 1 shared project, and 4 sample tasks.")
    print(f"Demo password for both accounts: {DEMO_PASSWORD}")
    print("Accounts: maya@example.com, arjun@example.com")


if __name__ == "__main__":
    main()
