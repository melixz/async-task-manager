.PHONY: help up down build logs clean migrate migrate-create test lint format dev-setup	

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Запустить сервисы (PostgreSQL + RabbitMQ)
	docker-compose up -d

down: ## Остановить сервисы
	docker-compose down

build: ## Собрать Docker-образ
	docker build -t async-task-manager .

logs: ## Показать логи сервисов
	docker-compose logs -f

clean: ## Очистить все контейнеры и volumes
	docker-compose down -v
	docker system prune -f

migrate: ## Применить миграции
	uv run alembic upgrade head

migrate-create: ## Создать новую миграцию
	uv run alembic revision --autogenerate -m "$(message)"

test: ## Запустить тесты
	uv run pytest

lint: ## Проверить код линтером
	uv run ruff check .

format: ## Отформатировать код
	uv run ruff format .

dev-setup: ## Настройка окружения для разработки
	@echo "Запуск сервисов..."
	docker-compose up -d
	@echo "Ожидание готовности PostgreSQL..."
	@until docker-compose exec -T postgres pg_isready -U user -d async_task_manager; do sleep 1; done
	@echo "Применение миграций..."
	uv run alembic upgrade head
	@echo "Готово! Сервисы запущены и миграции применены."