
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.database import get_db

from app.routers.project_router import router as project_router
from app.routers.auth_router import router as auth_router
from app.routers.project_member_router import (
    router as project_member_router,
    requests_router as project_join_requests_router
)
from app.routers import task_router
from app.routers import my_task_router
from app.routers import websocket_router
from app.routers import comment_router
from app.routers import activity_router
from app.routers import user_router

app = FastAPI(
    title="TaskFlow API",
    description="Collaborative Project and Task Management Application",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
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
app.include_router(project_join_requests_router)
app.include_router(task_router.router)
app.include_router(my_task_router.router)
app.include_router(websocket_router.router)
app.include_router(comment_router.router)
app.include_router(activity_router.router)
app.include_router(user_router.router)
