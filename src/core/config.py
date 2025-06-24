from pydantic import BaseSettings, PostgresDsn, AmqpDsn


class Settings(BaseSettings):
    """
    Класс конфигурации приложения.

    Атрибуты:
        database_url: строка подключения к PostgreSQL (PostgresDsn)
        rabbitmq_url: строка подключения к RabbitMQ (AmqpDsn)
    """

    database_url: PostgresDsn
    rabbitmq_url: AmqpDsn

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
