from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class EmailStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class EmailRequest(BaseModel):
    recipient: EmailStr
    subject: str
    body: str


class EmailResponse(BaseModel):
    id: int
    recipient: str
    subject: str
    status: EmailStatus
    task_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class EmailStatusResponse(BaseModel):
    task_id: str
    status: EmailStatus
    recipient: str
    subject: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
