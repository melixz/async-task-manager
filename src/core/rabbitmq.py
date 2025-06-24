import uuid
from typing import Optional, Dict
import aio_pika
from aio_pika import Message, DeliveryMode, ExchangeType
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue
import json
import logging
from src.core.config import settings

logger = logging.getLogger(__name__)


class RabbitMQManager:
    """Менеджер для работы с RabbitMQ очередями задач."""

    def __init__(self):
        self.connection: Optional[AbstractConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self.task_exchange = None
        self.queues: Dict[str, AbstractQueue] = {}

    async def connect(self) -> None:
        """Установить соединение с RabbitMQ."""
        try:
            self.connection = await aio_pika.connect_robust(str(settings.rabbitmq_url))
            self.channel = await self.connection.channel()

            await self.channel.set_qos(prefetch_count=1)

            self.task_exchange = await self.channel.declare_exchange(
                "tasks", ExchangeType.DIRECT, durable=True
            )

            await self._setup_queues()

            logger.info("Подключение к RabbitMQ установлено")

        except Exception as e:
            logger.error(f"Ошибка подключения к RabbitMQ: {e}")
            raise

    async def _setup_queues(self) -> None:
        """Настройка очередей для разных приоритетов."""
        priorities = ["HIGH", "MEDIUM", "LOW"]

        for priority in priorities:
            queue_name = f"tasks.{priority.lower()}"
            queue = await self.channel.declare_queue(queue_name, durable=True)

            await queue.bind(self.task_exchange, routing_key=priority)
            self.queues[priority] = queue

            logger.info(f"Очередь {queue_name} создана и привязана")

    async def publish_task(self, task_id: uuid.UUID, priority: str) -> None:
        """
        Отправить задачу в очередь по приоритету.

        Args:
            task_id: UUID задачи
            priority: Приоритет задачи (HIGH, MEDIUM, LOW)
        """
        if not self.task_exchange:
            raise RuntimeError("RabbitMQ не подключен")

        message_body = {"task_id": str(task_id), "priority": priority}

        message = Message(
            json.dumps(message_body).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json",
            message_id=str(uuid.uuid4()),
        )

        try:
            await self.task_exchange.publish(message, routing_key=priority)
            logger.info(f"Задача {task_id} отправлена в очередь {priority}")
        except Exception as e:
            logger.error(f"Ошибка отправки задачи {task_id}: {e}")
            raise

    async def consume_tasks(self, priority: str, callback) -> None:
        """
        Начать прослушивание очереди для обработки задач.

        Args:
            priority: Приоритет очереди (HIGH, MEDIUM, LOW)
            callback: Асинхронная функция для обработки задач
        """
        if priority not in self.queues:
            raise ValueError(f"Очередь для приоритета {priority} не найдена")

        queue = self.queues[priority]

        try:
            await queue.consume(callback, no_ack=False)
            logger.info(f"Начат consume очереди {priority}")
        except Exception as e:
            logger.error(f"Ошибка consume очереди {priority}: {e}")
            raise

    async def close(self) -> None:
        """Закрыть соединение с RabbitMQ."""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Соединение с RabbitMQ закрыто")


rabbitmq_manager = RabbitMQManager()


async def get_rabbitmq_manager() -> RabbitMQManager:
    """Получить экземпляр RabbitMQ менеджера."""
    if not rabbitmq_manager.connection:
        await rabbitmq_manager.connect()
    return rabbitmq_manager
