"""
Email client module for Promora.

This module provides functionality to connect to email servers and retrieve verification codes
from emails sent by platforms during account registration.
"""

import imaplib
import email
import re
import time
import random
from datetime import datetime, timedelta
from email.header import decode_header
from typing import Dict, List, Optional, Tuple, Any

from utils.logger import logger


class EmailClient:
    """Email client for retrieving verification codes from registration emails."""
    
    def __init__(self, email_address: str, password: str, imap_server: str = "imap.gmail.com", imap_port: int = 993):
        """Initialize the email client.
        
        Args:
            email_address: Email address to connect with
            password: Password or app password for the email account
            imap_server: IMAP server address (default: imap.gmail.com)
            imap_port: IMAP server port (default: 993)
        """
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.mail = None
        self.connected = False
        
        self.platform_patterns = {
            "x": {
                "subject_patterns": [
                    r"Verify your Twitter account",
                    r"Twitter verification code",
                    r"Your Twitter verification code",
                    r"X verification code",
                    r"Verify your X account"
                ],
                "sender_patterns": [
                    r"verify@twitter.com",
                    r"info@twitter.com",
                    r"no-reply@twitter.com",
                    r"verify@x.com",
                    r"info@x.com",
                    r"no-reply@x.com"
                ],
                "code_patterns": [
                    r"verification code is: (\d+)",
                    r"verification code: (\d+)",
                    r"code: (\d+)",
                    r"code is (\d+)",
                    r"<strong>(\d+)</strong>",
                    r"(\d{6})"  # Common 6-digit code pattern
                ],
                "link_patterns": [
                    r"href=[\"'](https?://(?:www\.)?(?:twitter|x)\.com/account/verify[^\"']+)[\"']",
                    r"href=[\"'](https?://(?:www\.)?(?:twitter|x)\.com/i/redirect[^\"']+)[\"']",
                    r"(https?://(?:www\.)?(?:twitter|x)\.com/account/verify[^\s\"'<>]+)",
                    r"(https?://(?:www\.)?(?:twitter|x)\.com/i/redirect[^\s\"'<>]+)"
                ]
            },
            "zhihu": {
                "subject_patterns": [
                    r"知乎验证码",
                    r"知乎注册验证",
                    r"Zhihu verification code",
                    r"Zhihu verification"
                ],
                "sender_patterns": [
                    r"no-reply@zhihu.com",
                    r"verify@zhihu.com",
                    r"service@zhihu.com"
                ],
                "code_patterns": [
                    r"验证码为：(\d+)",
                    r"验证码：(\d+)",
                    r"verification code is: (\d+)",
                    r"verification code: (\d+)",
                    r"code: (\d+)",
                    r"(\d{6})"  # Common 6-digit code pattern
                ],
                "link_patterns": [
                    r"href=[\"'](https?://(?:www\.)?zhihu\.com/email_verify[^\"']+)[\"']",
                    r"(https?://(?:www\.)?zhihu\.com/email_verify[^\s\"'<>]+)"
                ]
            },
            "linkedin": {
                "subject_patterns": [
                    r"LinkedIn verification code",
                    r"Your LinkedIn verification code",
                    r"LinkedIn security code",
                    r"Verify your LinkedIn account",
                    r"Complete your LinkedIn sign up"
                ],
                "sender_patterns": [
                    r"security-noreply@linkedin.com",
                    r"linkedin@linkedin.com",
                    r"no-reply@linkedin.com",
                    r"member@linkedin.com"
                ],
                "code_patterns": [
                    r"verification code is: (\d+)",
                    r"verification code: (\d+)",
                    r"security code: (\d+)",
                    r"code: (\d+)",
                    r"(\d{6})"  # Common 6-digit code pattern
                ],
                "link_patterns": [
                    r"href=[\"'](https?://(?:www\.)?linkedin\.com/e/[^\"']+)[\"']",
                    r"href=[\"'](https?://(?:www\.)?linkedin\.com/checkpoint/[^\"']+)[\"']",
                    r"(https?://(?:www\.)?linkedin\.com/e/[^\s\"'<>]+)",
                    r"(https?://(?:www\.)?linkedin\.com/checkpoint/[^\s\"'<>]+)"
                ]
            },
            "medium": {
                "subject_patterns": [
                    r"Verify your Medium account",
                    r"Medium verification code",
                    r"Your Medium verification code",
                    r"Verify your email on Medium",
                    r"Complete your Medium registration"
                ],
                "sender_patterns": [
                    r"noreply@medium.com",
                    r"verify@medium.com",
                    r"info@medium.com",
                    r"team@medium.com"
                ],
                "code_patterns": [
                    r"verification code is: (\d+)",
                    r"verification code: (\d+)",
                    r"code: (\d+)",
                    r"code is (\d+)",
                    r"(\d{6})"  # Common 6-digit code pattern
                ],
                "link_patterns": [
                    r"href=[\"'](https?://(?:www\.)?medium\.com/m/verify[^\"']+)[\"']",
                    r"href=[\"'](https?://(?:www\.)?medium\.com/m/confirm[^\"']+)[\"']",
                    r"(https?://(?:www\.)?medium\.com/m/verify[^\s\"'<>]+)",
                    r"(https?://(?:www\.)?medium\.com/m/confirm[^\s\"'<>]+)"
                ]
            }
        }
    
    def connect(self) -> bool:
        """Connect to the email server.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mail.login(self.email_address, self.password)
            self.connected = True
            logger.info(f"Successfully connected to email server: {self.imap_server}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to email server: {str(e)}")
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the email server."""
        if self.mail and self.connected:
            try:
                self.mail.logout()
                logger.info("Disconnected from email server")
            except Exception as e:
                logger.error(f"Error disconnecting from email server: {str(e)}")
            finally:
                self.connected = False
                self.mail = None
    
    def _decode_email_subject(self, subject: str) -> str:
        """Decode email subject.
        
        Args:
            subject: Email subject to decode
            
        Returns:
            Decoded subject
        """
        decoded_parts = []
        for part, encoding in decode_header(subject):
            if isinstance(part, bytes):
                if encoding:
                    try:
                        decoded_parts.append(part.decode(encoding))
                    except:
                        decoded_parts.append(part.decode('utf-8', errors='replace'))
                else:
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(part)
        return ''.join(decoded_parts)
    
    def _get_email_body(self, msg: email.message.Message) -> str:
        """Extract email body from message.
        
        Args:
            msg: Email message
            
        Returns:
            Email body text
        """
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                    except:
                        try:
                            body = part.get_payload(decode=True).decode('latin-1')
                        except:
                            body = str(part.get_payload(decode=True))
                    break
                elif content_type == "text/html" and "attachment" not in content_disposition and not body:
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                    except:
                        try:
                            body = part.get_payload(decode=True).decode('latin-1')
                        except:
                            body = str(part.get_payload(decode=True))
        else:
            content_type = msg.get_content_type()
            if content_type == "text/plain" or content_type == "text/html":
                try:
                    body = msg.get_payload(decode=True).decode('utf-8')
                except:
                    try:
                        body = msg.get_payload(decode=True).decode('latin-1')
                    except:
                        body = str(msg.get_payload(decode=True))
        
        return body
    
    def _extract_verification_code(self, body: str, subject: str, platform: str) -> Optional[str]:
        """Extract verification code from email body.
        
        Args:
            body: Email body text
            subject: Email subject
            platform: Platform name (x, zhihu, linkedin, medium)
            
        Returns:
            Verification code if found, None otherwise
        """
        if platform.lower() not in self.platform_patterns:
            logger.warning(f"No patterns defined for platform: {platform}")
            return None
        
        patterns = self.platform_patterns[platform.lower()]["code_patterns"]
        
        for pattern in patterns:
            match = re.search(pattern, body)
            if match:
                return match.group(1)
        
        for pattern in patterns:
            match = re.search(pattern, subject)
            if match:
                return match.group(1)
        
        return None
        
    def _extract_verification_link(self, body: str, platform: str) -> Optional[str]:
        """Extract verification link from email body.
        
        Args:
            body: Email body text
            platform: Platform name (x, zhihu, linkedin, medium)
            
        Returns:
            Verification link if found, None otherwise
        """
        if platform.lower() not in self.platform_patterns:
            logger.warning(f"No patterns defined for platform: {platform}")
            return None
        
        if "link_patterns" not in self.platform_patterns[platform.lower()]:
            logger.warning(f"No link patterns defined for platform: {platform}")
            return None
        
        patterns = self.platform_patterns[platform.lower()]["link_patterns"]
        
        for pattern in patterns:
            match = re.search(pattern, body)
            if match:
                link = match.group(1)
                logger.info(f"Found verification link for {platform}: {link}")
                return link
        
        return None
    
    def _is_verification_email(self, subject: str, sender: str, platform: str) -> bool:
        """Check if an email is a verification email for the specified platform.
        
        Args:
            subject: Email subject
            sender: Email sender
            platform: Platform name (x, zhihu, linkedin, medium)
            
        Returns:
            True if the email is a verification email, False otherwise
        """
        if platform.lower() not in self.platform_patterns:
            return False
        
        platform_patterns = self.platform_patterns[platform.lower()]
        
        subject_match = any(re.search(pattern, subject, re.IGNORECASE) for pattern in platform_patterns["subject_patterns"])
        
        sender_match = any(re.search(pattern, sender, re.IGNORECASE) for pattern in platform_patterns["sender_patterns"])
        
        return subject_match or sender_match
    
    def get_verification_code(self, platform: str, minutes: int = 5, max_attempts: int = 10, delay: int = 5) -> Optional[str]:
        """Get verification code from emails for a specific platform.
        
        Args:
            platform: Platform name (x, zhihu, linkedin, medium)
            minutes: Number of minutes to look back for emails (default: 5)
            max_attempts: Maximum number of attempts to check for new emails (default: 10)
            delay: Delay between attempts in seconds (default: 5)
            
        Returns:
            Verification code if found, None otherwise
        """
        if not self.connected and not self.connect():
            logger.error("Not connected to email server")
            return None
        
        platform = platform.lower()
        
        date_threshold = (datetime.now() - timedelta(minutes=minutes)).strftime("%d-%b-%Y")
        
        for attempt in range(max_attempts):
            try:
                self.mail.select("INBOX")
                
                status, messages = self.mail.search(None, f'(SINCE "{date_threshold}")')
                
                if status != "OK":
                    logger.error(f"Error searching for emails: {status}")
                    continue
                
                email_ids = messages[0].split()
                
                for email_id in reversed(email_ids):
                    status, msg_data = self.mail.fetch(email_id, "(RFC822)")
                    
                    if status != "OK":
                        logger.error(f"Error fetching email {email_id}: {status}")
                        continue
                    
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    subject = self._decode_email_subject(msg["Subject"] or "")
                    sender = msg["From"] or ""
                    
                    if self._is_verification_email(subject, sender, platform):
                        logger.info(f"Found verification email for {platform}: {subject}")
                        
                        body = self._get_email_body(msg)
                        
                        code = self._extract_verification_code(body, subject, platform)
                        
                        if code:
                            logger.info(f"Extracted verification code for {platform}: {code}")
                            return code
                
                if attempt < max_attempts - 1:
                    random_delay = delay + random.uniform(0.5, 2.0)
                    logger.info(f"No verification code found for {platform}, waiting {random_delay:.2f}s before retrying...")
                    time.sleep(random_delay)
            
            except Exception as e:
                logger.error(f"Error getting verification code: {str(e)}")
                random_delay = delay + random.uniform(0.5, 2.0)
                time.sleep(random_delay)
        
        logger.warning(f"No verification code found for {platform} after {max_attempts} attempts")
        return None
    
    def get_verification_link(self, platform: str, minutes: int = 5, max_attempts: int = 10, delay: int = 5) -> Optional[str]:
        """Get verification link from emails for a specific platform.
        
        Args:
            platform: Platform name (x, zhihu, linkedin, medium)
            minutes: Number of minutes to look back for emails (default: 5)
            max_attempts: Maximum number of attempts to check for new emails (default: 10)
            delay: Delay between attempts in seconds (default: 5)
            
        Returns:
            Verification link if found, None otherwise
        """
        if not self.connected and not self.connect():
            logger.error("Not connected to email server")
            return None
        
        platform = platform.lower()
        
        date_threshold = (datetime.now() - timedelta(minutes=minutes)).strftime("%d-%b-%Y")
        
        for attempt in range(max_attempts):
            try:
                self.mail.select("INBOX")
                
                status, messages = self.mail.search(None, f'(SINCE "{date_threshold}")')
                
                if status != "OK":
                    logger.error(f"Error searching for emails: {status}")
                    continue
                
                email_ids = messages[0].split()
                
                for email_id in reversed(email_ids):
                    status, msg_data = self.mail.fetch(email_id, "(RFC822)")
                    
                    if status != "OK":
                        logger.error(f"Error fetching email {email_id}: {status}")
                        continue
                    
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    subject = self._decode_email_subject(msg["Subject"] or "")
                    sender = msg["From"] or ""
                    
                    if self._is_verification_email(subject, sender, platform):
                        logger.info(f"Found verification email for {platform}: {subject}")
                        
                        body = self._get_email_body(msg)
                        
                        link = self._extract_verification_link(body, platform)
                        
                        if link:
                            logger.info(f"Extracted verification link for {platform}: {link}")
                            return link
                
                if attempt < max_attempts - 1:
                    random_delay = delay + random.uniform(0.5, 2.0)
                    logger.info(f"No verification link found for {platform}, waiting {random_delay:.2f}s before retrying...")
                    time.sleep(random_delay)
            
            except Exception as e:
                logger.error(f"Error getting verification link: {str(e)}")
                random_delay = delay + random.uniform(0.5, 2.0)
                time.sleep(random_delay)
        
        logger.warning(f"No verification link found for {platform} after {max_attempts} attempts")
        return None
    
    def wait_for_verification_code(self, platform: str, timeout_minutes: int = 10, check_interval: int = 10) -> Optional[str]:
        """Wait for a verification code to arrive for a specific platform.
        
        Args:
            platform: Platform name (x, zhihu, linkedin, medium)
            timeout_minutes: Maximum time to wait in minutes (default: 10)
            check_interval: Interval between checks in seconds (default: 10)
            
        Returns:
            Verification code if found, None otherwise
        """
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=timeout_minutes)
        
        logger.info(f"Waiting for verification code for {platform} (timeout: {timeout_minutes} minutes)")
        
        while datetime.now() < end_time:
            remaining_seconds = (end_time - datetime.now()).total_seconds()
            
            if remaining_seconds <= 0:
                break
            
            code = self.get_verification_code(platform, minutes=timeout_minutes)
            
            if code:
                return code
            
            random_interval = check_interval + random.uniform(1.0, 5.0)
            
            wait_time = min(random_interval, remaining_seconds)
            
            logger.info(f"No verification code yet, waiting {wait_time:.2f}s before checking again...")
            time.sleep(wait_time)
        
        logger.warning(f"Timeout waiting for verification code for {platform}")
        return None
        
    def wait_for_verification_link(self, platform: str, timeout_minutes: int = 10, check_interval: int = 10) -> Optional[str]:
        """Wait for a verification link to arrive for a specific platform.
        
        Args:
            platform: Platform name (x, zhihu, linkedin, medium)
            timeout_minutes: Maximum time to wait in minutes (default: 10)
            check_interval: Interval between checks in seconds (default: 10)
            
        Returns:
            Verification link if found, None otherwise
        """
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=timeout_minutes)
        
        logger.info(f"Waiting for verification link for {platform} (timeout: {timeout_minutes} minutes)")
        
        while datetime.now() < end_time:
            remaining_seconds = (end_time - datetime.now()).total_seconds()
            
            if remaining_seconds <= 0:
                break
            
            link = self.get_verification_link(platform, minutes=timeout_minutes)
            
            if link:
                return link
            
            random_interval = check_interval + random.uniform(1.0, 5.0)
            
            wait_time = min(random_interval, remaining_seconds)
            
            logger.info(f"No verification link yet, waiting {wait_time:.2f}s before checking again...")
            time.sleep(wait_time)
        
        logger.warning(f"Timeout waiting for verification link for {platform}")
        return None


class EmailClientFactory:
    """Factory for creating email clients."""
    
    @staticmethod
    def create_client(email_address: str, password: str, provider: str = "gmail") -> EmailClient:
        """Create an email client for a specific provider.
        
        Args:
            email_address: Email address to connect with
            password: Password or app password for the email account
            provider: Email provider (gmail, outlook, yahoo, etc.)
            
        Returns:
            EmailClient instance
        """
        provider = provider.lower()
        
        if provider == "gmail":
            return EmailClient(email_address, password, "imap.gmail.com", 993)
        elif provider == "outlook" or provider == "hotmail":
            return EmailClient(email_address, password, "outlook.office365.com", 993)
        elif provider == "yahoo":
            return EmailClient(email_address, password, "imap.mail.yahoo.com", 993)
        elif provider == "aol":
            return EmailClient(email_address, password, "imap.aol.com", 993)
        elif provider == "zoho":
            return EmailClient(email_address, password, "imap.zoho.com", 993)
        elif provider == "protonmail":
            return EmailClient(email_address, password, "imap.protonmail.ch", 993)
        else:
            logger.warning(f"Unknown email provider: {provider}, using default settings")
            return EmailClient(email_address, password)
