"""
Core Email Service Module

This module provides email services specifically for facility management functionality.
It handles facility invitations, notifications, and administrative communications.

Key functionalities:
- Facility invitation emails
- Welcome emails for new facility members
- Administrative notifications
- Subscription and billing notifications
- Training assignment notifications

Dependencies:
- emails: Email sending library
- jinja2: Template rendering
- app.utils.email_utils: Base email functionality
"""

import logging
from typing import Optional
from pydantic import EmailStr
from app.utils.email_utils import send_email
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def send_facility_invitation_email(
    email: EmailStr,
    facility_name: str,
    invitation_code: str,
    admin_name: str,
    personal_message: Optional[str] = None
) -> bool:
    """Send facility invitation email to a user."""
    try:
        subject = f"You're invited to join {facility_name}"
        
        # Create invitation URL
        base_url = settings.FRONTEND_URL or "http://localhost:5174"
        invitation_url = f"{base_url}/join-facility/{invitation_code}"
        
        # HTML template for facility invitation
        html_template = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Team Invitation</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #1e3a8a; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
                .content { background-color: #f8fafc; padding: 30px; border-radius: 0 0 8px 8px; }
                .button { 
                    display: inline-block; 
                    background-color: #1e3a8a; 
                    color: white !important; 
                    padding: 18px 40px; 
                    text-decoration: none !important; 
                    border-radius: 12px; 
                    margin: 25px auto;
                    font-weight: bold;
                    font-size: 18px;
                    border: 3px solid #1e3a8a;
                    box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    transition: all 0.3s ease;
                }
                .button:hover {
                    background-color: #1e40af;
                    border-color: #1e40af;
                    box-shadow: 0 6px 16px rgba(30, 58, 138, 0.4);
                    transform: translateY(-2px);
                }
                .button:active {
                    transform: translateY(0);
                    box-shadow: 0 2px 8px rgba(30, 58, 138, 0.3);
                }
                .message-box { 
                    background-color: white; 
                    border-left: 4px solid #1e3a8a;
                    padding: 15px; 
                    margin: 20px 0;
                    border-radius: 4px;
                }
                .footer { 
                    text-align: center; 
                    padding: 20px; 
                    font-size: 12px; 
                    color: #6b7280; 
                    border-top: 1px solid #e5e7eb;
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>You're invited to join {{ facility_name }}</h1>
                </div>
                
                <div class="content">
                    <p>Hello!</p>
                    
                    <p><strong>{{ admin_name }}</strong> has invited you to join their team at <strong>{{ facility_name }}</strong>.</p>
                    
                    {% if personal_message %}
                    <div class="message-box">
                        <p><strong>Message from {{ admin_name }}:</strong></p>
                        <p><em>"{{ personal_message }}"</em></p>
                    </div>
                    {% endif %}
                    
                    <div style="text-align: center; margin: 40px 0; padding: 20px 0; background-color: #f8fafc; border-radius: 8px;">
                        <a href="{{ invitation_url }}" class="button" style="display: inline-block; background-color: #1e3a8a; color: white !important; padding: 18px 40px; text-decoration: none !important; border-radius: 12px; font-weight: bold; font-size: 18px; border: 3px solid #1e3a8a; box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3); text-transform: uppercase; letter-spacing: 1px;">Accept Invitation</a>
                    </div>
                    
                    <p>Click the button above to create your account and join the team. Your information will be pre-filled to make setup quick and easy.</p>
                    
                    <p><small>
                        If the button doesn't work, copy and paste this link into your browser:<br>
                        <a href="{{ invitation_url }}">{{ invitation_url }}</a>
                    </small></p>
                    
                    <p><small>
                        This invitation expires in 7 days. If you have questions, contact {{ admin_name }}.
                    </small></p>
                </div>
                
                <div class="footer">
                    <p>This invitation was sent by {{ admin_name }} from {{ facility_name }}.</p>
                    <p>EnCompliance - Childcare Compliance & Facility Management</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        context = {
            "facility_name": facility_name,
            "invitation_code": invitation_code,
            "invitation_url": invitation_url,
            "admin_name": admin_name,
            "personal_message": personal_message,
            "__template_override__": html_template
        }
        
        success = send_email(
            subject=subject,
            recipient=email,
            template_name="facility_invitation",
            context=context
        )
        
        if success:
            logger.info(f"Facility invitation email sent successfully to {email}")
        else:
            logger.error(f"Failed to send facility invitation email to {email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending facility invitation email: {str(e)}")
        return False


def send_facility_welcome_email(
    email: EmailStr,
    user_name: str,
    facility_name: str,
    admin_name: str
) -> bool:
    """Send welcome email to new facility member."""
    try:
        subject = f"Welcome to {facility_name} on EnCompliance!"
        
        html_template = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to the Team - EnCompliance</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #059669; color: white; padding: 20px; text-align: center; }
                .content { background-color: #f0fdf4; padding: 30px; }
                .button { 
                    display: inline-block; 
                    background-color: #059669; 
                    color: white; 
                    padding: 12px 24px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                }
                .footer { background-color: #e5e7eb; padding: 20px; font-size: 12px; color: #6b7280; }
                .feature-box { 
                    background-color: white; 
                    border-left: 4px solid #059669; 
                    padding: 15px; 
                    margin: 15px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome to the Team, {{ user_name }}!</h1>
                </div>
                
                <div class="content">
                    <p>Congratulations! You have successfully joined <strong>{{ facility_name }}</strong> on the EnCompliance platform.</p>
                    
                    <p>{{ admin_name }} has added you to the team, and you now have access to all facility resources and training materials.</p>
                    
                    <h3>Here's what you can do now:</h3>
                    
                    <div class="feature-box">
                        <h4>📚 Access Training Materials</h4>
                        <p>Browse personalized training modules and track your progress through compliance requirements.</p>
                    </div>
                    
                    <div class="feature-box">
                        <h4>📅 View Team Calendar</h4>
                        <p>Stay up-to-date with facility-wide training sessions, meetings, and important compliance deadlines.</p>
                    </div>
                    
                    <div class="feature-box">
                        <h4>🤖 Use AI Assistant</h4>
                        <p>Get instant answers to compliance questions and access regulatory guidance 24/7.</p>
                    </div>
                    
                    <div class="feature-box">
                        <h4>📊 Track Your Progress</h4>
                        <p>Monitor your compliance achievements and see upcoming requirements at a glance.</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{ dashboard_url }}" class="button">Go to Dashboard</a>
                    </div>
                    
                    <h3>Need Help Getting Started?</h3>
                    <ul>
                        <li>Contact {{ admin_name }} for facility-specific guidance</li>
                        <li>Check out the Help section in your dashboard</li>
                        <li>Reach out to our support team if you have technical questions</li>
                    </ul>
                    
                    <p>We're excited to have you on board and look forward to supporting your compliance journey!</p>
                </div>
                
                <div class="footer">
                    <p>You joined {{ facility_name }} managed by {{ admin_name }}.</p>
                    <p>EnCompliance - Healthcare Compliance Platform</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        dashboard_url = f"{settings.FRONTEND_URL or 'http://localhost:5174'}/dashboard"
        
        context = {
            "user_name": user_name,
            "facility_name": facility_name,
            "admin_name": admin_name,
            "dashboard_url": dashboard_url,
            "__template_override__": html_template
        }
        
        success = send_email(
            subject=subject,
            recipient=email,
            template_name="facility_welcome",
            context=context
        )
        
        if success:
            logger.info(f"Welcome email sent successfully to {email}")
        else:
            logger.error(f"Failed to send welcome email to {email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending welcome email: {str(e)}")
        return False


def send_training_assignment_email(
    email: EmailStr,
    user_name: str,
    training_title: str,
    facility_name: str,
    due_date: str,
    assigned_by: str
) -> bool:
    """Send training assignment notification email."""
    try:
        subject = f"New Training Assignment: {training_title}"
        
        html_template = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Training Assignment - EnCompliance</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #7c3aed; color: white; padding: 20px; text-align: center; }
                .content { background-color: #faf5ff; padding: 30px; }
                .button { 
                    display: inline-block; 
                    background-color: #7c3aed; 
                    color: white; 
                    padding: 12px 24px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                }
                .footer { background-color: #e5e7eb; padding: 20px; font-size: 12px; color: #6b7280; }
                .assignment-box { 
                    background-color: white; 
                    border: 1px solid #d1d5db; 
                    border-radius: 8px; 
                    padding: 20px; 
                    margin: 20px 0;
                }
                .due-date { 
                    background-color: #fef3c7; 
                    border-left: 4px solid #f59e0b; 
                    padding: 10px; 
                    margin: 15px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📚 New Training Assignment</h1>
                </div>
                
                <div class="content">
                    <p>Hello {{ user_name }},</p>
                    
                    <p>You have been assigned a new training module by {{ assigned_by }} at {{ facility_name }}.</p>
                    
                    <div class="assignment-box">
                        <h3>{{ training_title }}</h3>
                        
                        <div class="due-date">
                            <strong>⏰ Due Date:</strong> {{ due_date }}
                        </div>
                        
                        <p>Please complete this training module by the due date to maintain your compliance status.</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{ training_url }}" class="button">Start Training</a>
                    </div>
                    
                    <h3>What's Next?</h3>
                    <ol>
                        <li>Click "Start Training" to access the module</li>
                        <li>Complete all sections and assessments</li>
                        <li>Track your progress in your dashboard</li>
                        <li>Contact {{ assigned_by }} if you have questions</li>
                    </ol>
                    
                    <p><small>
                        This assignment is part of {{ facility_name }}'s compliance program. 
                        Completing your training on time helps ensure our facility maintains the highest standards of care.
                    </small></p>
                </div>
                
                <div class="footer">
                    <p>Training assigned by {{ assigned_by }} at {{ facility_name }}.</p>
                    <p>EnCompliance - Healthcare Compliance Platform</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        training_url = f"{settings.FRONTEND_URL or 'http://localhost:5174'}/training"
        
        context = {
            "user_name": user_name,
            "training_title": training_title,
            "facility_name": facility_name,
            "due_date": due_date,
            "assigned_by": assigned_by,
            "training_url": training_url,
            "__template_override__": html_template
        }
        
        success = send_email(
            subject=subject,
            recipient=email,
            template_name="training_assignment",
            context=context
        )
        
        if success:
            logger.info(f"Training assignment email sent successfully to {email}")
        else:
            logger.error(f"Failed to send training assignment email to {email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending training assignment email: {str(e)}")
        return False 