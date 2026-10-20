"""
OTP Utilities Module

This module provides core OTP (One-Time Password) functionality for the EnCompliance application.
It handles OTP generation, hashing, verification, and communication channels.

Key functionalities:
- Random OTP generation
- OTP hashing and verification
- Email OTP delivery
- SMS OTP delivery
- OTP expiry management
"""

import random
import string
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import requests
import logging

from app.models.otp import OTP, OTPType
from app.auth.utils import get_password_hash, verify_password
from app.core.config import get_settings

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Get application settings
settings = get_settings()

# SMTP Settings from application settings
SMTP_SERVER = os.getenv("SMTP_HOST", settings.SMTP_HOST or "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", str(settings.SMTP_PORT)))
SMTP_USERNAME = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER") or settings.SMTP_USERNAME or settings.SMTP_USER or ""
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", settings.SMTP_PASSWORD or "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL") or os.getenv("EMAILS_FROM_EMAIL") or settings.SMTP_FROM_EMAIL or settings.EMAILS_FROM_EMAIL or "noreply@encompliance.com"
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME") or settings.SMTP_FROM_NAME or settings.EMAILS_FROM_NAME

# SMS Gateway Settings (using a simple HTTP-based gateway for demonstration)
SMS_GATEWAY_URL = os.getenv("SMS_GATEWAY_URL", "")
SMS_GATEWAY_API_KEY = os.getenv("SMS_GATEWAY_API_KEY", "")

# OTP Settings
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))
MAX_OTP_ATTEMPTS = int(os.getenv("MAX_OTP_ATTEMPTS", "3"))

def generate_otp(length=OTP_LENGTH):
    """Generate a random numeric OTP of specified length"""
    # In development mode (when SMTP is not configured), use a fixed OTP for testing
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return "123456"  # Fixed OTP for development/testing
    
    return ''.join(random.choices(string.digits, k=length))

def create_otp_record(db: Session, user_id: int, recipient: str, otp_type: OTPType, otp_code: str):
    """Create an OTP record in the database"""
    # Hash the OTP for security
    otp_hash = get_password_hash(otp_code)
    
    # Calculate expiry time
    expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    
    # Create OTP record
    otp_record = OTP(
        user_id=user_id,
        otp_type=otp_type,
        otp_hash=otp_hash,
        recipient=recipient,
        expires_at=expires_at
    )
    
    # Add to database
    db.add(otp_record)
    db.commit()
    db.refresh(otp_record)
    
    return otp_record

def verify_otp(db: Session, user_id: int, recipient: str, otp_type: OTPType, otp_code: str):
    """Verify an OTP code against database records"""
    # Find the most recent OTP for this user and recipient
    query = db.query(OTP).filter(
        OTP.recipient == recipient,
        OTP.otp_type == otp_type,
        OTP.is_verified == False
    )
    
    # Add user_id filter only if user_id is not None
    if user_id is not None:
        query = query.filter(OTP.user_id == user_id)
    else:
        query = query.filter(OTP.user_id.is_(None))
    
    otp_record = query.order_by(OTP.created_at.desc()).first()
    
    if not otp_record:
        return False, "No OTP found for verification"
    
    # Check if OTP has expired
    if otp_record.is_expired():
        return False, "OTP has expired"
    
    # Check if too many verification attempts
    if otp_record.verification_attempts >= MAX_OTP_ATTEMPTS:
        return False, "Too many verification attempts"
    
    # Increase attempt counter
    otp_record.increase_attempt()
    db.commit()
    
    # Verify OTP
    if verify_password(otp_code, otp_record.otp_hash):
        # Mark as verified
        otp_record.is_verified = True
        db.commit()
        return True, "OTP verified successfully"
    
    return False, "Invalid OTP code"

def send_email_otp(recipient: str, otp_code: str):
    """Send OTP via email"""
    try:
        # Development mode: If SMTP is not configured, just log the OTP
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            logger.warning(f"SMTP not configured. Development mode: OTP for {recipient} is: {otp_code}")
            print(f"🔑 DEVELOPMENT MODE - OTP for {recipient}: {otp_code}")  # Also print to console
            return True, "OTP sent successfully (Development mode - check logs)"
        
        # Check if SMTP credentials are properly configured
        if not SMTP_SERVER or not SMTP_PORT:
            logger.error("SMTP server or port not configured")
            return False, "Email service not properly configured: SMTP server settings missing"
            
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = recipient
        msg['Subject'] = "Your EnCompliance Verification Code"
        
        # Create message body
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; text-align: center;">
                    <h2 style="color: #333;">EnCompliance Verification Code</h2>
                    <p style="font-size: 16px; color: #555;">Your verification code is:</p>
                    <div style="background-color: #eef2ff; padding: 15px; font-size: 24px; font-weight: bold; letter-spacing: 5px; border-radius: 4px; margin: 20px 0;">
                        {otp_code}
                    </div>
                    <p style="font-size: 14px; color: #777;">This code will expire in {OTP_EXPIRY_MINUTES} minutes.</p>
                    <p style="font-size: 14px; color: #777;">If you didn't request this code, please ignore this email.</p>
                </div>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to SMTP server
        logger.info(f"Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        
        # Login with credentials
        if SMTP_USERNAME and SMTP_PASSWORD:
            logger.info(f"Logging in with username: {SMTP_USERNAME}")
            try:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            except smtplib.SMTPAuthenticationError:
                logger.error("SMTP authentication failed - invalid credentials")
                return False, "Email service authentication failed: Invalid credentials"
        else:
            logger.error("SMTP credentials not provided")
            return False, "Email service not properly configured: SMTP credentials missing"
        
        # Send email
        try:
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email OTP sent to {recipient}")
            return True, "OTP sent successfully"
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False, f"Failed to send email: {str(e)}"
    
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Failed to send email OTP: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def send_sms_otp(recipient: str, otp_code: str):
    """Send OTP via SMS"""
    try:
        # Check if SMS gateway is configured
        if not SMS_GATEWAY_URL or not SMS_GATEWAY_API_KEY:
            logger.warning("SMS gateway not configured. OTP code would be sent to " + recipient)
            # For development, just log the OTP
            logger.info(f"SMS OTP for {recipient}: {otp_code}")
            return True, "OTP sent successfully (Development mode)"
        
        # For production, use the configured SMS gateway
        payload = {
            "api_key": SMS_GATEWAY_API_KEY,
            "to": recipient,
            "message": f"Your EnCompliance verification code is: {otp_code}. Valid for {OTP_EXPIRY_MINUTES} minutes."
        }
        
        response = requests.post(SMS_GATEWAY_URL, json=payload)
        
        if response.status_code == 200:
            logger.info(f"SMS OTP sent to {recipient}")
            return True, "OTP sent successfully"
        else:
            error_message = f"SMS gateway error: {response.text}"
            logger.error(error_message)
            return False, error_message
            
    except Exception as e:
        logger.error(f"Failed to send SMS OTP: {str(e)}")
        return False, f"Failed to send OTP: {str(e)}" 