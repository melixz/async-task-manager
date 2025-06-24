# async-task-manager

Асинхронный сервис управления задачами с RabbitMQ и PostgreSQL.

## Функциональность

- **REST API** для управления задачами (создание, получение, отмена)
- **RabbitMQ** для асинхронной обработки задач по приоритетам
- **Система приоритетов** - HIGH/MEDIUM/LOW с отдельными очередями
- **PostgreSQL** для хранения задач
- **Статусы задач** - NEW/PENDING/IN_PROGRESS/COMPLETED/FAILED/CANCELLED
- **Docker** для простого развертывания

## Быстрый старт

### 1. Запуск всех сервисов
```bash
# Клонирование и переход в каталог
git clone <repo-url>
cd async-task-manager

# Запуск всех сервисов (API + Worker + DB + RabbitMQ)
make up

# Применение миграций
make migrate
```

### 2. Проверка работы
```bash
# API доступно по адресу: http://localhost:8000
# Swagger UI: http://localhost:8000/docs
# RabbitMQ Management: http://localhost:15672 (guest/guest)

# Создание задачи
curl -X POST "http://localhost:8000/api/v1/tasks/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Тестовая задача",
    "description": "Описание задачи",
    "priority": "HIGH"
  }'

# Получение списка задач
curl "http://localhost:8000/api/v1/tasks/"
```

## Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   FastAPI App   │────│    RabbitMQ     │────│  Task Worker    │
│    (REST API)   │    │   (3 Queues)    │    │   (Consumer)    │
│                 │    │                 │    │                 │
└─────────┬───────┘    └─────────────────┘    └─────────┬───────┘
          │                                             │
          │            ┌─────────────────┐              │
          └────────────│   PostgreSQL    │──────────────┘
                       │   (Database)    │
                       └─────────────────┘
```

## API Endpoints

### Создание задачи
```http
POST /api/v1/tasks/
Content-Type: application/json

{
  "title": "Название задачи",
  "description": "Описание задачи",
  "priority": "HIGH"  // HIGH, MEDIUM, LOW
}
```

### Получение списка задач
```http
GET /api/v1/tasks/?status=NEW&priority=HIGH&skip=0&limit=10
```

### Получение задачи по ID
```http
GET /api/v1/tasks/{task_id}
```

### Получение статуса задачи
```http
GET /api/v1/tasks/{task_id}/status
```

### Отмена задачи
```http
DELETE /api/v1/tasks/{task_id}
```

## Разработка

### Настройка окружения
```bash
# Установка зависимостей
uv sync

# Запуск только базовых сервисов (DB + RabbitMQ)
make api-only

# Применение миграций
make migrate

# Запуск API в режиме разработки
make dev

# Запуск воркера (в отдельном терминале)
make worker
```

### Полезные команды
```bash
make help           # Показать все команды
make up             # Запустить все сервисы
make down           # Остановить все сервисы
make logs           # Показать логи
make test           # Запустить тесты
make lint           # Проверить код
make format         # Отформатировать код
```

### Переменные окружения
```bash
# .env файл (создать локально)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/async_task_manager
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

## Система приоритетов

Задачи обрабатываются в отдельных очередях по приоритетам:

- **HIGH** - высокий приоритет (2 секунды обработки)
- **MEDIUM** - средний приоритет (5 секунд обработки)  
- **LOW** - низкий приоритет (10 секунд обработки)

Воркер одновременно слушает все очереди, но обрабатывает задачи справедливо (prefetch_count=1).

## Статусы задач

- **NEW** - задача создана, но не отправлена в очередь
- **PENDING** - задача отправлена в RabbitMQ и ожидает обработки
- **IN_PROGRESS** - задача обрабатывается воркером
- **COMPLETED** - задача успешно выполнена
- **FAILED** - ошибка при выполнении задачи
- **CANCELLED** - задача отменена пользователем

## Технологии

- **Python 3.12** - основной язык
- **FastAPI** - веб-фреймворк
- **PostgreSQL 14** - база данных
- **RabbitMQ 3.12** - брокер сообщений
- **SQLAlchemy 2.0** - ORM
- **Alembic** - миграции
- **aio-pika** - асинхронный клиент RabbitMQ
- **Pydantic v2** - валидация данных
- **Docker & Docker Compose** - контейнеризация

## Мониторинг

- **RabbitMQ Management UI**: http://localhost:15672
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health 

## Тестирование

```bash
# Запуск тестов
make test

# Тестирование API
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "priority": "HIGH"}'
```