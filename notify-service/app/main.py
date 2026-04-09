from fastapi import FastAPI
from app.api.router import router as email_router
import logging

# Конфигурация логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализируем FastAPI приложение
app = FastAPI(
    title="Notify Hub - Email Service",
    description="Асинхронный сервис отправки email на базе Celery и RabbitMQ",
    version="0.1.0"
)

# Подключаем роутеры
app.include_router(email_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "service": "notify-hub"}


@app.get("/", tags=["Root"])
async def root():
    """Главная страница API"""
    return {
        "message": "Welcome to Notify Hub - Email Service",
        "endpoints": {
            "send_email": "POST /emails/send",
            "check_status": "GET /emails/status/{task_id}",
            "list_emails": "GET /emails/list",
            "get_email": "GET /emails/{email_id}",
            "health": "GET /health",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
