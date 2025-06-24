import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Enum, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    """Базовый класс для всех моделей проекта."""

    pass


class TaskStatus(enum.Enum):
    """Перечисление возможных статусов задачи."""

    NEW = "NEW"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskPriority(enum.Enum):
    """Перечисление приоритетов задачи."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Task(Base):
    """
    SQLAlchemy-модель задачи для асинхронного менеджера задач.

    Атрибуты:
        id: Уникальный идентификатор задачи (UUID).
        title: Название задачи.
        description: Описание задачи.
        priority: Приоритет задачи (LOW, MEDIUM, HIGH).
        status: Текущий статус задачи.
        created_at: Дата и время создания.
        started_at: Дата и время начала выполнения.
        finished_at: Дата и время завершения.
        result: Результат выполнения (если есть).
        error: Информация об ошибке (если есть).
    """

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="task_priority"), nullable=False
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"), nullable=False, default=TaskStatus.NEW
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
