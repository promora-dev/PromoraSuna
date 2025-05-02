"""
Email sender module for Promora.

This module provides functionality to send emails from Promora.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Dict, Any

from utils.logger import logger


def send_email(
    sender_email: str,
    sender_password: str,
    recipient_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
    cc: Optional[list] = None,
    bcc: Optional[list] = None
) -> Dict[str, Any]:
    """Send an email.
    
    Args:
        sender_email: Email address to send from
        sender_password: Password or app password for the email account
        recipient_email: Email address to send to
        subject: Email subject
        body_text: Plain text email body
        body_html: HTML email body (optional)
        smtp_server: SMTP server address (default: smtp.gmail.com)
        smtp_port: SMTP server port (default: 587)
        cc: List of CC recipients (optional)
        bcc: List of BCC recipients (optional)
        
    Returns:
        Dictionary with status and message
    """
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email
    
    if cc:
        message["Cc"] = ", ".join(cc)
    if bcc:
        message["Bcc"] = ", ".join(bcc)
    
    part1 = MIMEText(body_text, "plain")
    message.attach(part1)
    
    if body_html:
        part2 = MIMEText(body_html, "html")
        message.attach(part2)
    
    try:
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(sender_email, sender_password)
            
            recipients = [recipient_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
                
            server.sendmail(sender_email, recipients, message.as_string())
            
            logger.info(f"Email sent successfully to {recipient_email}")
            return {
                "status": "success",
                "message": f"Email sent successfully to {recipient_email}",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        error_message = f"Failed to send email: {str(e)}"
        logger.error(error_message)
        return {
            "status": "error",
            "message": error_message,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def determine_smtp_settings(email_address: str) -> Dict[str, Any]:
    """Determine SMTP settings based on email domain.
    
    Args:
        email_address: Email address to determine settings for
        
    Returns:
        Dictionary with SMTP server and port
    """
    domain = email_address.split('@')[-1].lower()
    
    smtp_settings = {
        "gmail.com": {"server": "smtp.gmail.com", "port": 587},
        "outlook.com": {"server": "smtp.office365.com", "port": 587},
        "hotmail.com": {"server": "smtp.office365.com", "port": 587},
        "yahoo.com": {"server": "smtp.mail.yahoo.com", "port": 587},
        "aol.com": {"server": "smtp.aol.com", "port": 587},
        "zoho.com": {"server": "smtp.zoho.com", "port": 587},
        "protonmail.com": {"server": "smtp.protonmail.ch", "port": 587},
        "promora.ai": {"server": "smtp.gmail.com", "port": 587}  # Assuming promora.ai uses Gmail
    }
    
    if domain in smtp_settings:
        return smtp_settings[domain]
    else:
        return {"server": f"smtp.{domain}", "port": 587}


if __name__ == "__main__":
    # or secure configuration in production
    import os
    
    sender = os.getenv("EMAIL_SENDER", "example@example.com")
    password = os.getenv("EMAIL_PASSWORD", "")  # Load from environment variable
    recipient = os.getenv("EMAIL_RECIPIENT", "recipient@example.com")
    
    if not password:
        print("Please set EMAIL_PASSWORD environment variable")
        exit(1)
    
    smtp_settings = determine_smtp_settings(sender)
    
    result = send_email(
        sender_email=sender,
        sender_password=password,
        recipient_email=recipient,
        subject="Promora Test Email",
        body_text="This is a test email from Promora.\n\nThis email is for testing the email sending functionality.",
        body_html="""
        <html>
        <body>
            <h2>Promora Test Email</h2>
            <p>This is a test email from Promora.</p>
            <p>This email is for testing the email sending functionality.</p>
            <hr>
            <p><em>Promora - AI-driven Virtual CMO</em></p>
        </body>
        </html>
        """,
        smtp_server=smtp_settings["server"],
        smtp_port=smtp_settings["port"]
    )
    
    print(result)
