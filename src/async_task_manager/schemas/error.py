from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    """Детали ошибки."""

    detail: str = Field(..., description="Описание ошибки")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"detail": "Задача не найдена"},
                {"detail": "Задачу нельзя отменить из текущего статуса"},
            ]
        }
    )


class ValidationError(BaseModel):
    """Ошибка валидации данных."""

    detail: list[dict] = Field(..., description="Детали ошибок валидации")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "detail": [
                        {
                            "type": "string_pattern_mismatch",
                            "loc": ["body", "priority"],
                            "msg": "String should match pattern '^(LOW|MEDIUM|HIGH)$'",
                            "input": "INVALID",
                        }
                    ]
                }
            ]
        }
    )


class HealthStatus(BaseModel):
    """Статус здоровья сервиса."""

    database: bool = Field(..., description="Статус подключения к базе данных")
    rabbitmq: bool = Field(..., description="Статус подключения к RabbitMQ")
    status: bool = Field(..., description="Общий статус сервиса")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"database": True, "rabbitmq": True, "status": True},
                {"database": False, "rabbitmq": True, "status": False},
            ]
        }
    )
