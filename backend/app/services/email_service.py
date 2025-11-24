# backend/app/services/email_service.py
"""
Email service for sending notifications.
For production, use SendGrid, AWS SES, or similar service.
"""
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..core.config import settings


class EmailService:
    """Handle email sending operations."""
    
    def __init__(self):
        """Initialize email service."""
        # For development: Print to console
        # For production: Configure SMTP or external service
        self.mode = "smtp" 
    
    def send_password_reset_email(
        self, 
        email: str, 
        reset_token: str,
        username: str
    ) -> bool:
        """
        Send password reset email.
        
        Args:
            email: Recipient email
            reset_token: JWT reset token
            username: User's username
        
        Returns:
            True if sent successfully
        """
        # Construct reset URL
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        # Email content
        subject = "Reset Your Password"
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">Password Reset Request</h2>
                    
                    <p>Hi {username},</p>
                    
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" 
                           style="background-color: #2563eb; 
                                  color: white; 
                                  padding: 12px 30px; 
                                  text-decoration: none; 
                                  border-radius: 5px;
                                  display: inline-block;">
                            Reset Password
                        </a>
                    </div>
                    
                    <p style="color: #666; font-size: 14px;">
                        Or copy and paste this link into your browser:<br>
                        <a href="{reset_url}">{reset_url}</a>
                    </p>
                    
                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        ⏰ This link will expire in <strong>1 hour</strong> for security reasons.
                    </p>
                    
                    <p style="color: #666; font-size: 14px;">
                        If you didn't request this password reset, please ignore this email or contact support if you have concerns.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="color: #999; font-size: 12px;">
                        This is an automated message, please do not reply to this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        text_body = f"""
        Password Reset Request
        
        Hi {username},
        
        We received a request to reset your password. Click the link below to create a new password:
        
        {reset_url}
        
        This link will expire in 1 hour for security reasons.
        
        If you didn't request this password reset, please ignore this email.
        """
        
        if self.mode == "console":
            # Development: Print to console
            print("\n" + "="*80)
            print("📧 PASSWORD RESET EMAIL")
            print("="*80)
            print(f"To: {email}")
            print(f"Subject: {subject}")
            print("\n" + text_body)
            print("="*80 + "\n")
            return True
        
        elif self.mode == "smtp":
            # Production SMTP (Gmail, Outlook, etc.)
            return self._send_via_smtp(email, subject, html_body, text_body)
        
        elif self.mode == "sendgrid":
            # Production: SendGrid API
            return self._send_via_sendgrid(email, subject, html_body)
        
        return False
    
    def _send_via_smtp(self, to_email: str, subject: str, html_body: str,text_body: str) -> bool:
        """Send email via SMTP server."""
        try:
            from ..core.config import settings
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = settings.SMTP_FROM_EMAIL
            message["To"] = to_email
            
            # Add both plain text and HTML versions
            text_part = MIMEText(text_body, "plain")
            html_part = MIMEText(html_body, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(message)
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to send email via SMTP: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _send_via_sendgrid(self, to_email: str, subject: str, html_body: str) -> bool:
 
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            message = Mail(
                from_email=settings.SMTP_FROM_EMAIL,
                to_emails=to_email,
                subject=subject,
                html_content=html_body
            )
            
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
            
            return response.status_code == 202
        
        except Exception as e:
            print(f"Failed to send email via SendGrid: {e}")
            return False


# Singleton instance
email_service = EmailService()