
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.database import get_db

from app.routers.project_router import router as project_router

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

app.include_router(project_router)
