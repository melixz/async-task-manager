import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    """Схема для создания задачи."""

    title: str = Field(..., example="Сделать тестовое задание")
    description: Optional[str] = Field(None, example="Подробное описание задачи")
    priority: str = Field(..., example="HIGH", pattern="^(LOW|MEDIUM|HIGH)$")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Сделать тестовое задание",
                    "description": "Подробное описание задачи",
                    "priority": "HIGH",
                }
            ]
        }
    )


class TaskRead(BaseModel):
    """Схема для вывода задачи."""

    id: uuid.UUID
    title: str
    description: Optional[str]
    priority: str
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    result: Optional[str]
    error: Optional[str]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "b3b7c7e2-8c2e-4e2a-9c2e-7e2a8c2e4e2a",
                    "title": "Сделать тестовое задание",
                    "description": "Подробное описание задачи",
                    "priority": "HIGH",
                    "status": "NEW",
                    "created_at": "2024-06-20T12:00:00Z",
                    "started_at": None,
                    "finished_at": None,
                    "result": None,
                    "error": None,
                }
            ]
        },
    )


class TaskStatusRead(BaseModel):
    """Схема для получения статуса задачи."""

    id: uuid.UUID
    status: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {"id": "b3b7c7e2-8c2e-4e2a-9c2e-7e2a8c2e4e2a", "status": "IN_PROGRESS"}
            ]
        },
    )


class TaskFilter(BaseModel):
    """Схема для фильтрации и пагинации задач."""

    status: Optional[str] = Field(None, example="NEW")
    priority: Optional[str] = Field(None, example="HIGH")
    skip: int = Field(0, ge=0, example=0)
    limit: int = Field(10, ge=1, le=100, example=10)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"status": "NEW", "priority": "HIGH", "skip": 0, "limit": 10}]
        },
    )
