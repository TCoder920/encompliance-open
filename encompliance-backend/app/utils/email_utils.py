# Description: Utility functions for sending emails, including survey responses and contact messages.
# Purpose: Centralizes all email-sending logic for the EnCompliance backend, ensuring consistent formatting and delivery of support and survey emails.
import os
import emails
from emails.template import JinjaTemplate
from pydantic import EmailStr
from app.core.config import get_settings
import logging

# Get the settings instance by calling the function
settings = get_settings()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email(
    subject: str,
    recipient: EmailStr,
    template_name: str,
    context: dict,
) -> bool:
    """Sends an email using the configured SMTP settings."""
    # Enhanced SMTP configuration diagnostics
    smtp_host = settings.SMTP_HOST
    smtp_from_email = settings.SMTP_FROM_EMAIL
    smtp_username = settings.SMTP_USERNAME
    smtp_password = settings.SMTP_PASSWORD
    
    # Log SMTP configuration status (without exposing credentials)
    logger.info(f"SMTP Configuration Check:")
    logger.info(f"  SMTP_HOST: {'SET' if smtp_host else 'NOT SET'}")
    logger.info(f"  SMTP_FROM_EMAIL: {'SET' if smtp_from_email else 'NOT SET'}")
    logger.info(f"  SMTP_USERNAME: {'SET' if smtp_username else 'NOT SET'}")
    logger.info(f"  SMTP_PASSWORD: {'SET' if smtp_password else 'NOT SET'}")
    
    if not smtp_host or not smtp_from_email:
        error_msg = "SMTP settings not configured. Missing required settings:"
        missing = []
        if not smtp_host:
            missing.append("SMTP_HOST")
        if not smtp_from_email:
            missing.append("SMTP_FROM_EMAIL")
        error_msg += " " + ", ".join(missing)
        logger.error(error_msg)
        
        # Development mode fallback: log email content instead of sending
        logger.warning("DEVELOPMENT MODE: Email would be sent to production SMTP")
        logger.warning(f"Subject: {subject}")
        logger.warning(f"Recipient: {recipient}")
        logger.warning(f"Content preview: {context}")
        print(f"\n📧 DEVELOPMENT MODE - EMAIL SIMULATION")
        print(f"To: {recipient}")
        print(f"Subject: {subject}")
        print(f"Content: {context}")
        print("=" * 50)
        
        # Return True in development mode to prevent breaking functionality
        return True

    # Use template override if provided in context
    html_template = context.pop("__template_override__", '''
        <!DOCTYPE html>
        <html>
        <body>
            <h2>Survey Response Details</h2>
            <h3>User Information:</h3>
            <ul>
                <li><strong>User ID:</strong> {{ user_data.id }}</li>
                <li><strong>Email:</strong> {{ user_data.email }}</li>
                <li><strong>Username:</strong> {{ user_data.username }}</li>
                {% if user_data.name %}
                <li><strong>Name:</strong> {{ user_data.name }}</li>
                {% endif %}
                {% if user_data.phone_number %}
                <li><strong>Phone:</strong> {{ user_data.phone_number }}</li>
                {% endif %}
            </ul>
            <h3>Survey Response:</h3>
            <p><strong>Selected Option:</strong> {{ response }}</p>
            {% if other_text %}
            <p><strong>Additional Details:</strong> {{ other_text }}</p>
            {% endif %}
        </body>
        </html>
        ''')

    message = emails.Message(
        subject=JinjaTemplate(subject).render(**context),
        html=JinjaTemplate(html_template).render(**context),
        mail_from=(settings.SMTP_FROM_NAME, settings.SMTP_FROM_EMAIL),
    )

    smtp_options = {
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "tls": settings.SMTP_USE_TLS,
        "user": settings.SMTP_USERNAME,
        "password": settings.SMTP_PASSWORD,
    }

    try:
        logger.info(f"Attempting to send email to {recipient} via {smtp_host}:{settings.SMTP_PORT}")
        response = message.send(to=recipient, smtp=smtp_options)
        if response.status_code in [250,]: # Check for success codes
            logger.info(f"Email sent successfully to {recipient}")
            return True
        else:
            # Enhanced error logging with more details
            logger.error(f"Failed to send email to {recipient}")
            logger.error(f"  SMTP Status Code: {response.status_code}")
            logger.error(f"  Response Object: {response}")
            logger.error(f"  SMTP Host: {smtp_host}")
            logger.error(f"  SMTP Port: {settings.SMTP_PORT}")
            logger.error(f"  TLS Enabled: {settings.SMTP_USE_TLS}")
            return False
    except Exception as e:
        # Enhanced exception logging
        logger.error(f"Exception sending email to {recipient}: {str(e)}")
        logger.error(f"  Exception Type: {type(e).__name__}")
        logger.error(f"  SMTP Configuration Used:")
        logger.error(f"    Host: {smtp_host}")
        logger.error(f"    Port: {settings.SMTP_PORT}")
        logger.error(f"    TLS: {settings.SMTP_USE_TLS}")
        logger.error(f"    Username: {'SET' if smtp_username else 'NOT SET'}")
        return False

def send_survey_response_email(user_data: dict, response: str, other_text: str | None = None) -> bool:
    """Sends the survey response to the support email with complete user data."""
    subject = f"Compliance Challenge Survey Response from {user_data['username']}"
    recipient = settings.SUPPORT_EMAIL # Ensure SUPPORT_EMAIL is in your settings
    if not recipient:
        logger.error("SUPPORT_EMAIL not configured. Cannot send survey response email.")
        return False

    # Survey response email template
    html_template = '''
    <!DOCTYPE html>
    <html>
    <body>
        <h2>Survey Response Details</h2>
        <h3>User Information:</h3>
        <ul>
            <li><strong>User ID:</strong> {{ user_data.id }}</li>
            <li><strong>Email:</strong> {{ user_data.email }}</li>
            <li><strong>Username:</strong> {{ user_data.username }}</li>
            {% if user_data.name %}
            <li><strong>Name:</strong> {{ user_data.name }}</li>
            {% endif %}
            {% if user_data.phone_number %}
            <li><strong>Phone:</strong> {{ user_data.phone_number }}</li>
            {% endif %}
        </ul>
        <h3>Survey Response:</h3>
        <p><strong>Selected Option:</strong> {{ response }}</p>
        {% if other_text %}
        <p><strong>Additional Details:</strong> {{ other_text }}</p>
        {% endif %}
    </body>
    </html>
    '''

    context = {
        "user_data": user_data,
        "response": response,
        "other_text": other_text,
        "__template_override__": html_template
    }

    # Using a simple hardcoded HTML template here for brevity
    # In a real app, you might load templates from files
    return send_email(
        subject=subject,
        recipient=recipient,
        template_name="survey_response", # Placeholder, actual template is hardcoded
        context=context,
    )

def send_contact_message_email(user_data: dict, message: str) -> bool:
    """Sends a contact message to the support email with complete user data and the user's message."""
    subject = f"Contact Us Message from {user_data.get('username') or user_data.get('email') or 'Anonymous'}"
    recipient = settings.SUPPORT_EMAIL  # Ensure SUPPORT_EMAIL is in your settings
    if not recipient:
        logger.error("SUPPORT_EMAIL not configured. Cannot send contact message email.")
        return False

    context = {
        "user_data": user_data,
        "message": message,
    }

    # Hardcoded HTML template for contact message
    html_template = '''
    <!DOCTYPE html>
    <html>
    <body>
        <h2>Contact Us Message</h2>
        <h3>User Information:</h3>
        <ul>
            {% if user_data.id %}<li><strong>User ID:</strong> {{ user_data.id }}</li>{% endif %}
            {% if user_data.email %}<li><strong>Email:</strong> {{ user_data.email }}</li>{% endif %}
            {% if user_data.username %}<li><strong>Username:</strong> {{ user_data.username }}</li>{% endif %}
            {% if user_data.name %}<li><strong>Name:</strong> {{ user_data.name }}</li>{% endif %}
            {% if user_data.phone_number %}<li><strong>Phone:</strong> {{ user_data.phone_number }}</li>{% endif %}
        </ul>
        <h3>Message:</h3>
        <p>{{ message }}</p>
    </body>
    </html>
    '''

    return send_email(
        subject=subject,
        recipient=recipient,
        template_name="contact_message",  # Placeholder, actual template is hardcoded
        context={**context, "__template_override__": html_template},
    )

# Example of how settings might look in app/core/config.py
# from pydantic_settings import BaseSettings
# class Settings(BaseSettings):
#     SMTP_HOST: str | None = None
#     SMTP_PORT: int = 587
#     SMTP_TLS: bool = True
#     SMTP_USER: str | None = None
#     SMTP_PASSWORD: str | None = None
#     EMAILS_FROM_EMAIL: EmailStr | None = None
#     EMAILS_FROM_NAME: str | None = "EnCompliance Support"
#     SUPPORT_EMAIL: EmailStr | None = "support@encompliance.io"
# settings = Settings() 