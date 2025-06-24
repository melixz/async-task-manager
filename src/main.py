from fastapi import FastAPI
from src.api import task_router

app = FastAPI(title="Async Task Manager", version="1.0.0")

app.include_router(task_router, prefix="/api/v1")
