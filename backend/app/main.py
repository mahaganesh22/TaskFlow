
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.database import get_db

from app.routers.project_router import router as project_router
from app.routers.auth_router import router as auth_router
from app.routers.project_member_router import (
    router as project_member_router
)
from app.routers import task_router
from app.routers import my_task_router
from app.routers import websocket_router
from app.routers import comment_router

app = FastAPI(
    title="TaskFlow API",
    description="Collaborative Project and Task Management Application",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Welcome to TaskFlow API"
    }


@app.get("/health/database")
def check_database(db: Session = Depends(get_db)):

    db.execute(text("SELECT 1"))

    return {
        "database": "Connected successfully"
    }

app.include_router(auth_router)
app.include_router(project_router)
app.include_router(project_member_router)
app.include_router(task_router.router)
app.include_router(my_task_router.router)
app.include_router(websocket_router.router)
app.include_router(comment_router.router)
