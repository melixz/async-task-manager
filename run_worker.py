import asyncio
import logging

from async_task_manager.workers import run_worker

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("Запуск воркера обработки задач...")

    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Воркер остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка воркера: {e}")
        raise
