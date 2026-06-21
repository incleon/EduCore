import os
import logging
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

def get_mail_config() -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_USERNAME,
        MAIL_PORT=587,
        MAIL_SERVER="smtp.gmail.com",
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
        TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates" / "email"
    )

async def send_student_credentials(
    student_name: str,
    personal_email: str,
    student_id: str,
    institutional_email: str,
    generated_password: str
):
    """
    Sends the generated credentials to the student's personal email.
    """
    try:
        context = {
            "student_name": student_name,
            "student_id": student_id,
            "institutional_email": institutional_email,
            "generated_password": generated_password
        }
        
        message = MessageSchema(
            subject="Welcome to EduCore CMS - Your Account Credentials",
            recipients=[personal_email],
            template_body=context,
            subtype=MessageType.html
        )

        conf = get_mail_config()
        fm = FastMail(conf)
        await fm.send_message(message, template_name="student_welcome.html")
        logger.info(f"Successfully sent credentials email to {personal_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {personal_email}: {str(e)}")
        return False
