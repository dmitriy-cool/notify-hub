from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.email_schema import EmailRequest, EmailResponse, EmailStatusResponse
from app.services.email_service import EmailCRUD
from app.tasks.email import send_email
from app.models.email_model import EmailRecord

router = APIRouter(prefix="/emails", tags=["emails"])


@router.post("/send", response_model=EmailResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_email_endpoint(
    email_request: EmailRequest,
    db: AsyncSession = Depends(get_db)
):
    email_record = EmailRecord(
        recipient=email_request.recipient,
        subject=email_request.subject,
        body=email_request.body,
        status="PENDING",
        task_id=""  # Временно пустой
    )
    db.add(email_record)
    await db.commit()
    await db.refresh(email_record)
    
    # Ставим задачу в очередь Celery с использованием .apply_async()
    task = send_email.apply_async(
        args=[
            email_record.id,
            email_request.recipient,
            email_request.subject,
            email_request.body
        ],
        queue='email_queue',
        routing_key='send_email',
    )
    
    # Обновляем task_id в БД
    email_record.task_id = task.id
    await db.commit()
    await db.refresh(email_record)
    
    return email_record


@router.get("/status/{task_id}", response_model=EmailStatusResponse)
async def get_email_status(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):    
    email_record = await EmailCRUD.get_email_by_task_id(db, task_id)
    
    if not email_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email with task_id {task_id} not found"
        )

    return email_record


@router.get("/list", response_model=list[EmailResponse])
async def list_emails(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    
    emails = await EmailCRUD.get_all_emails(db, skip=skip, limit=limit)
    return emails


@router.get("/{email_id}", response_model=EmailStatusResponse)
async def get_email(
    email_id: int,
    db: AsyncSession = Depends(get_db)
):
    email_record = await EmailCRUD.get_email_by_id(db, email_id)
    
    if not email_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email with ID {email_id} not found"
        )
    
    return email_record
