from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Класс конфигурации приложения.

    Атрибуты:
        database_url: строка подключения к PostgreSQL
        rabbitmq_url: строка подключения к RabbitMQ
    """

    database_url: str = (
        "postgresql+asyncpg://user:password@localhost/async_task_manager"
    )
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
