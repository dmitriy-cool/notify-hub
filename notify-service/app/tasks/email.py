import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from app.tasks.celery_app import app
from app.models.email_model import EmailRecord, EmailStatus
from app.core.database import get_sync_db

logger = logging.getLogger(__name__)


class MockSMTP:
    def __init__(self, *args, **kwargs):
        logger.info(f"MockSMTP initialized with args: {args}, kwargs: {kwargs}")
    
    def sendmail(self, from_addr, to_addr, msg):
        logger.info(f"MockSMTP.sendmail called:")
        logger.info(f"  From: {from_addr}")
        logger.info(f"  To: {to_addr}")
        logger.info(f"  Message preview: {msg[:200]}...")
        return {}
    
    def quit(self):
        logger.info("MockSMTP.quit called")
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.quit()


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(self, email_id: int, recipient: str, subject: str, body: str):
    """
    Celery-задача для отправки email с retry logic.
    
    Args:
        email_id: ID записи в БД
        recipient: Адрес получателя
        subject: Тема письма
        body: Тело письма
    
    Returns:
        dict с результатом отправки
    """
    db: Session = get_sync_db()
    
    try:
        email_record = db.query(EmailRecord).filter(
            EmailRecord.id == email_id
        ).first()
        
        if not email_record:
            logger.error(f"Email record {email_id} not found")
            return {"status": "failed", "error": "Email record not found"}
        
        email_record.status = EmailStatus.PROCESSING
        db.commit()
        
        logger.info(f"Sending email to {recipient} (ID: {email_id})")
        
        msg = MIMEMultipart()
        msg['From'] = os.getenv('SMTP_USER', 'noreply@example.com')
        msg['To'] = recipient
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        use_mock = os.getenv('USE_MOCK_SMTP', 'true').lower() == 'true'
        
        if use_mock:
            with MockSMTP() as smtp:
                smtp.sendmail(msg['From'], recipient, msg.as_string())
        else:
            smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp:
                    smtp.login(smtp_user, smtp_password)
                    smtp.sendmail(msg['From'], recipient, msg.as_string())
            else:
                with smtplib.SMTP(smtp_host, smtp_port) as smtp:
                    smtp.starttls()
                    smtp.login(smtp_user, smtp_password)
                    smtp.sendmail(msg['From'], recipient, msg.as_string())
        
        email_record.status = EmailStatus.SUCCESS
        db.commit()
        
        logger.info(f"Email successfully sent to {recipient} (ID: {email_id})")
        
        return {
            "status": "success",
            "email_id": email_id,
            "recipient": recipient,
            "message": f"Email sent to {recipient}"
        }
    
    except smtplib.SMTPException as exc:
        logger.warning(f"SMTP error for email {email_id}: {exc}. Retrying...")
        
        # Retry с exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    
    except Exception as exc:
        logger.error(f"Unexpected error sending email {email_id}: {exc}")
        
        if isinstance(exc, self.MaxRetriesExceededError):
            email_record = db.query(EmailRecord).filter(
                EmailRecord.id == email_id
            ).first()
            if email_record:
                email_record.status = EmailStatus.FAILED
                email_record.error_message = str(exc)
                db.commit()
        else:
            try:
                raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
            except self.MaxRetriesExceededError:
                email_record = db.query(EmailRecord).filter(
                    EmailRecord.id == email_id
                ).first()
                if email_record:
                    email_record.status = EmailStatus.FAILED
                    email_record.error_message = str(exc)
                    db.commit()
        
        return {
            "status": "failed",
            "email_id": email_id,
            "error": str(exc)
        }
    
    finally:
        db.close()
