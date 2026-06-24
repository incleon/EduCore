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
        MAIL_FROM=settings.MAIL_FROM or settings.MAIL_USERNAME,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=bool(settings.MAIL_USERNAME and settings.MAIL_PASSWORD),
        VALIDATE_CERTS=settings.MAIL_VALIDATE_CERTS,
        MAIL_DEBUG=settings.MAIL_DEBUG,
        TIMEOUT=settings.MAIL_TIMEOUT,
        TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates" / "email"
    )


def is_email_service_configured() -> bool:
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        logger.warning(
            "Email service not configured. Set MAIL_USERNAME and MAIL_PASSWORD in .env to enable outgoing email. "
            "For Gmail, use an app password and configure MAIL_PORT=587, MAIL_STARTTLS=True, MAIL_SSL_TLS=False."
        )
        return False
    return True


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
    if not is_email_service_configured():
        return False

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
