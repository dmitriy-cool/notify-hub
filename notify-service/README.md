# 📧 Notify Hub - Email Service

Асинхронный сервис отправки email на базе Celery, RabbitMQ, FastAPI и PostgreSQL.

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                      NOTIFY HUB                             │
├─────────────┬──────────────────┬────────────────────────────┤
│  FastAPI    │   RabbitMQ       │   Celery Workers           │
│  (API)      │   (Message       │   (Task Execution)         │
│             │    Broker)       │                            │
│  8000       │   5672, 15672    │   Background Jobs          │
└─────────────┴──────────────────┴────────────────────────────┘
              │
        ┌─────┴─────┐
        │           │
    ┌───▼──┐   ┌───▼──┐
    │ PG   │   │Redis │
    │ 5434 │   │ 6379 │
    └──────┘   └──────┘
```

## 🚀 Быстрый старт

### 1. Docker Compose (1 команда)

```bash
docker-compose up
```

✅ Все сервисы запустятся автоматически:
- **API:** http://localhost:8000
- **RabbitMQ UI:** http://localhost:15672 (guest/guest)
- **Docs:** http://localhost:8000/docs

### 2. Отправить email (curl)

```bash
curl -X POST http://localhost:8000/emails/send \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "user@example.com",
    "subject": "Hello",
    "body": "Test email"
  }'
```

📋 Ответ:
```json
{
  "id": 1,
  "recipient": "user@example.com",
  "subject": "Hello",
  "status": "PENDING",
  "task_id": "email_1_abc123...",
  "created_at": "2026-04-09T12:00:00"
}
```

### 3. Проверить статус

```bash
curl http://localhost:8000/emails/status/email_1_abc123...
```

📋 Ответ:
```json
{
  "task_id": "email_1_abc123...",
  "status": "SUCCESS",
  "recipient": "user@example.com",
  "subject": "Hello",
  "error_message": null,
  "created_at": "2026-04-09T12:00:00",
  "updated_at": "2026-04-09T12:00:01"
}
```

## 📚 Документация

**[⚡ QUICK REFERENCE](QUICK_REFERENCE.md)** - Самое важное на одной странице

**[👉 Начните с INDEX.md](INDEX.md)** - Полный указатель документации

Подробная информация в:
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Полное описание архитектуры и жизненного цикла задачи
- **[TASK_LIFECYCLE.md](TASK_LIFECYCLE.md)** - Детальное описание стадий задачи с диаграммами
- **[EXAMPLES.md](EXAMPLES.md)** - Примеры использования API и Python кода
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Что реализовано и чеклист

## 🔑 Ключевые компоненты

### API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|---------|
| POST | `/emails/send` | Отправить email (асинхронно) |
| GET | `/emails/status/{task_id}` | Проверить статус |
| GET | `/emails/{email_id}` | Получить письмо по ID |
| GET | `/emails/list` | Список всех писем |
| GET | `/health` | Проверка здоровья сервиса |

### Celery Task

```python
@app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(self, email_id, recipient, subject, body):
    # Отправка email с retry logic
    # Exponential backoff: 60s → 120s → 240s
    # Мок SMTP для разработки
    # Сохранение результата в PostgreSQL и Redis
```

### RabbitMQ Configuration

- **Exchange:** `email_exchange` (тип: direct)
- **Queue:** `email_queue`
- **Routing Key:** `send_email`

**Это позволяет:**
- ✅ Точная маршрутизация задач
- ✅ Надежная доставка (durable)
- ✅ Масштабируемость (множество воркеров)

### Статусы письма

| Статус | Описание |
|--------|---------|
| PENDING | Ожидание обработки |
| PROCESSING | Воркер обрабатывает |
| SUCCESS | ✅ Успешно отправлено |
| FAILED | ❌ Ошибка после всех ретраев |

## ⚙️ Конфигурация

### Переменные окружения

```env
# БД
DATABASE_URL=postgresql+asyncpg://postgres:sanji@postgres_db:5432/notifhub_db

# Celery
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis:6379/0

# SMTP (разработка)
USE_MOCK_SMTP=true

# SMTP (production)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 🧪 Локальная разработка

### Требования

- Python 3.10+
- RabbitMQ
- PostgreSQL
- Redis

### Установка

```bash
# 1. Зависимости
pip install -r requirements.txt

# 2. Запустить FastAPI
uvicorn app.main:app --reload --port 8000

# 3. В отдельном терминале запустить Celery Worker
celery -A app.tasks.celery_app worker --loglevel=info
```

## 📊 Мониторинг

### RabbitMQ Management

http://localhost:15672 (guest/guest)

Смотреть:
- Queues: активные сообщения
- Connections: Celery workers
- Channels: активные каналы

### Celery Flower (опционально)

```bash
pip install flower
celery -A app.tasks.celery_app flower --port=5555
```

http://localhost:5555

## 🔍 Жизненный цикл задачи

```
1. POST /emails/send
   ↓
2. FastAPI валидирует данные
   ↓
3. Создает запись в PostgreSQL (PENDING)
   ↓
4. Ставит задачу в RabbitMQ
   ↓
5. Возвращает task_id (202 Accepted)
   ↓
6. Celery Worker получает задачу
   ↓
7. Обновляет статус на PROCESSING
   ↓
8. Отправляет email (мок SMTP или реальный)
   ↓
9. Обновляет статус на SUCCESS
   ↓
10. Сохраняет результат в Redis
   ↓
11. GET /emails/status/{task_id} возвращает SUCCESS
```

**При ошибке:**
- SMTP Exception → Retry (60s → 120s → 240s)
- После 3 ретраев → статус FAILED
- Ошибка сохранена в БД

## 📦 Dependencies

```
fastapi==0.128.0         # Web framework
celery==5.3.6            # Task queue
kombu==5.3.7             # Message routing
sqlalchemy==2.0.46       # ORM
asyncpg==0.29.0          # Async PostgreSQL
redis==7.1.0             # Cache & result backend
pydantic==2.12.5         # Data validation
```

## 🎯 MVP Features

✅ Async email sending
✅ Celery + RabbitMQ integration
✅ Direct exchange + single queue
✅ Mock SMTP for development
✅ Retry logic with exponential backoff
✅ Status tracking (PENDING → SUCCESS/FAILED)
✅ FastAPI + PostgreSQL + Redis
✅ Full API for task management

## 📝 TODO (Next Phase)

- [ ] Broadcast tasks (fanout exchange)
- [ ] Report generation (topic exchange)
- [ ] Task chaining (chain, group, chord)
- [ ] Authentication (JWT)
- [ ] Unit & integration tests
- [ ] API rate limiting
- [ ] Request logging & monitoring
- [ ] Flower UI integration
- [ ] Health checks for all services

## 📞 Support

Подробная документация в:
- [ARCHITECTURE.md](ARCHITECTURE.md) - Архитектура проекта
- [EXAMPLES.md](EXAMPLES.md) - Примеры использования

---

**Made with ❤️ using FastAPI, Celery, and RabbitMQ**
