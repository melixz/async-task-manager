import asyncio
import json
import uuid
import logging
from datetime import datetime, timezone
from aio_pika.abc import AbstractIncomingMessage
from src.core.rabbitmq import get_rabbitmq_manager
from src.core.db import async_session_maker
from src.models import Task, TaskStatus
from sqlalchemy import select, update

logger = logging.getLogger(__name__)


class TaskWorker:
    """Воркер для обработки задач из RabbitMQ очередей."""

    def __init__(self):
        self.rabbitmq = None
        self.running = False

    async def start(self) -> None:
        """Запуск воркера для всех приоритетов."""
        self.rabbitmq = await get_rabbitmq_manager()
        self.running = True

        priorities = ["HIGH", "MEDIUM", "LOW"]
        tasks = []

        for priority in priorities:
            task = asyncio.create_task(self._start_consumer(priority))
            tasks.append(task)

        logger.info("TaskWorker запущен для всех приоритетов")

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Ошибка в TaskWorker: {e}")
            raise

    async def _start_consumer(self, priority: str) -> None:
        """Запуск consumer для конкретного приоритета."""
        try:
            await self.rabbitmq.consume_tasks(
                priority, lambda message: self._process_message(message, priority)
            )
        except Exception as e:
            logger.error(f"Ошибка consumer для {priority}: {e}")
            raise

    async def _process_message(
        self, message: AbstractIncomingMessage, priority: str
    ) -> None:
        """
        Обработка сообщения из очереди.

        Args:
            message: Сообщение из RabbitMQ
            priority: Приоритет очереди
        """
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                task_id = uuid.UUID(body["task_id"])

                logger.info(f"Обработка задачи {task_id} из очереди {priority}")

                await self._execute_task(task_id)

                logger.info(f"Задача {task_id} успешно выполнена")

            except Exception as e:
                logger.error(f"Ошибка обработки сообщения: {e}")
                raise

    async def _execute_task(self, task_id: uuid.UUID) -> None:
        """
        Выполнение задачи по ID.

        Args:
            task_id: UUID задачи
        """
        async with async_session_maker() as session:
            try:
                result = await session.execute(select(Task).where(Task.id == task_id))
                task = result.scalar_one_or_none()

                if not task:
                    logger.warning(f"Задача {task_id} не найдена в БД")
                    return

                if task.status != TaskStatus.PENDING:
                    logger.warning(
                        f"Задача {task_id} имеет статус {task.status}, пропускаем"
                    )
                    return

                await session.execute(
                    update(Task)
                    .where(Task.id == task_id)
                    .values(
                        status=TaskStatus.IN_PROGRESS,
                        started_at=datetime.now(timezone.utc),
                    )
                )
                await session.commit()

                logger.info(f"Задача {task_id} переведена в статус IN_PROGRESS")

                result = await self._simulate_task_execution(task)

                await session.execute(
                    update(Task)
                    .where(Task.id == task_id)
                    .values(
                        status=TaskStatus.COMPLETED,
                        finished_at=datetime.now(timezone.utc),
                        result=result,
                    )
                )
                await session.commit()

                logger.info(f"Задача {task_id} завершена успешно")

            except Exception as e:
                logger.error(f"Ошибка выполнения задачи {task_id}: {e}")

                try:
                    await session.execute(
                        update(Task)
                        .where(Task.id == task_id)
                        .values(
                            status=TaskStatus.FAILED,
                            finished_at=datetime.now(timezone.utc),
                            error=str(e),
                        )
                    )
                    await session.commit()
                except Exception as update_error:
                    logger.error(
                        f"Ошибка обновления статуса задачи {task_id}: {update_error}"
                    )

                raise

    async def _simulate_task_execution(self, task: Task) -> str:
        """
        Симуляция выполнения задачи.
        В реальном приложении здесь была бы бизнес-логика.

        Args:
            task: Объект задачи

        Returns:
            Результат выполнения задачи
        """
        priority_delays = {"HIGH": 2, "MEDIUM": 5, "LOW": 10}

        delay = priority_delays.get(task.priority.value, 5)
        await asyncio.sleep(delay)

        return (
            f"Задача '{task.title}' выполнена успешно. Приоритет: {task.priority.value}"
        )

    async def stop(self) -> None:
        """Остановка воркера."""
        self.running = False
        if self.rabbitmq:
            await self.rabbitmq.close()
        logger.info("TaskWorker остановлен")


async def run_worker():
    """Запуск воркера задач."""
    worker = TaskWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    finally:
        await worker.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    asyncio.run(run_worker())
