from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Конфигурация приложения через переменные окружения.
    """

    DATABASE_URL: str = "postgresql+asyncpg://user:password@postgres:5432/async_task_manager"
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672//"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
