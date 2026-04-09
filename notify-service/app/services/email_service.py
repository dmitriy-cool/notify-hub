from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.email_model import EmailRecord, EmailStatus
from app.schemas.email_schema import EmailRequest


class EmailCRUD:
    """CRUD операции для email"""
    
    @staticmethod
    async def create_email(db: AsyncSession, email_data: EmailRequest, task_id: str):
        email_record = EmailRecord(
            recipient=email_data.recipient,
            subject=email_data.subject,
            body=email_data.body,
            task_id=task_id,
            status=EmailStatus.PENDING
        )
        db.add(email_record)
        await db.commit()
        await db.refresh(email_record)
        return email_record
    
    @staticmethod
    async def get_email_by_task_id(db: AsyncSession, task_id: str):
        """Получает запись о письме по task_id"""
        result = await db.execute(
            select(EmailRecord).where(EmailRecord.task_id == task_id)
        )
        return result.scalars().first()
    
    @staticmethod
    async def get_email_by_id(db: AsyncSession, email_id: int):
        """Получает запись о письме по ID"""
        result = await db.execute(
            select(EmailRecord).where(EmailRecord.id == email_id)
        )
        return result.scalars().first()
    
    @staticmethod
    async def get_all_emails(db: AsyncSession, skip: int = 0, limit: int = 100):
        """Получает список писем с пагинацией"""
        result = await db.execute(
            select(EmailRecord).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_emails_by_status(db: AsyncSession, status: EmailStatus, skip: int = 0, limit: int = 100):
        """Получает письма по статусу"""
        result = await db.execute(
            select(EmailRecord).where(
                EmailRecord.status == status
            ).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def update_email_status(db: AsyncSession, email_id: int, status: EmailStatus, error_message: str = None):
        """Обновляет статус письма"""
        result = await db.execute(
            select(EmailRecord).where(EmailRecord.id == email_id)
        )
        email_record = result.scalars().first()
        if email_record:
            email_record.status = status
            if error_message:
                email_record.error_message = error_message
            await db.commit()
            await db.refresh(email_record)
        return email_record
