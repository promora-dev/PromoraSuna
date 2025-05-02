"""
发送测试邮件脚本

此脚本用于发送测试邮件，测试邮件发送功能。
"""

import smtplib
import ssl
import socket
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_email(
    sender_email,
    sender_password,
    recipient_email,
    subject,
    body_text,
    body_html=None,
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    timeout=30,
    debug_level=1
):
    """发送邮件
    
    Args:
        sender_email: 发件人邮箱
        sender_password: 发件人密码
        recipient_email: 收件人邮箱
        subject: 邮件主题
        body_text: 纯文本邮件内容
        body_html: HTML邮件内容（可选）
        smtp_server: SMTP服务器地址
        smtp_port: SMTP服务器端口
        timeout: 连接超时时间（秒）
        debug_level: SMTP调试级别（0-2）
        
    Returns:
        包含状态和消息的字典
    """
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email
    
    part1 = MIMEText(body_text, "plain")
    message.attach(part1)
    
    if body_html:
        part2 = MIMEText(body_html, "html")
        message.attach(part2)
    
    logger.info(f"尝试从 {sender_email} 发送邮件到 {recipient_email}")
    logger.info(f"使用SMTP服务器: {smtp_server}:{smtp_port}")
    
    try:
        context = ssl.create_default_context()
        
        socket.setdefaulttimeout(timeout)
        
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=timeout)
        server.set_debuglevel(debug_level)
        
        logger.info("已连接到SMTP服务器")
        server.ehlo()
        
        logger.info("启动TLS")
        server.starttls(context=context)
        server.ehlo()
        
        logger.info("尝试登录")
        server.login(sender_email, sender_password)
        logger.info("登录成功")
        
        logger.info(f"发送邮件到 {recipient_email}")
        server.sendmail(sender_email, [recipient_email], message.as_string())
        logger.info("邮件发送成功")
        
        server.quit()
        
        return {
            "status": "success",
            "message": f"邮件成功发送到 {recipient_email}",
            "timestamp": datetime.now().isoformat()
        }
    except socket.timeout as e:
        error_message = f"连接超时: {str(e)}"
        logger.error(error_message)
        return {
            "status": "error",
            "message": error_message,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    except smtplib.SMTPAuthenticationError as e:
        error_message = f"认证失败: {str(e)}"
        logger.error(error_message)
        return {
            "status": "error",
            "message": error_message,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    except smtplib.SMTPException as e:
        error_message = f"SMTP错误: {str(e)}"
        logger.error(error_message)
        return {
            "status": "error",
            "message": error_message,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_message = f"发送邮件失败: {str(e)}"
        logger.error(error_message)
        return {
            "status": "error",
            "message": error_message,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def try_multiple_smtp_servers(
    sender_email,
    sender_password,
    recipient_email,
    subject,
    body_text,
    body_html=None
):
    """尝试使用多个SMTP服务器配置发送邮件
    
    Args:
        sender_email: 发件人邮箱
        sender_password: 发件人密码
        recipient_email: 收件人邮箱
        subject: 邮件主题
        body_text: 纯文本邮件内容
        body_html: HTML邮件内容（可选）
        
    Returns:
        包含状态和消息的字典
    """
    domain = sender_email.split('@')[-1].lower()
    
    smtp_configs = []
    
    if domain == "promora.ai":
        smtp_configs.extend([
            ("smtp.gmail.com", 587),
            ("smtp.office365.com", 587),
            ("smtp.promora.ai", 587),
            ("mail.promora.ai", 587),
            ("smtp.zoho.com", 587)
        ])
    elif domain == "gmail.com":
        smtp_configs.extend([
            ("smtp.gmail.com", 587),
            ("smtp.gmail.com", 465)
        ])
    else:
        smtp_configs.extend([
            (f"smtp.{domain}", 587),
            (f"mail.{domain}", 587),
            ("smtp.gmail.com", 587),
            ("smtp.office365.com", 587)
        ])
    
    for smtp_server, smtp_port in smtp_configs:
        logger.info(f"尝试SMTP服务器: {smtp_server}:{smtp_port}")
        
        result = send_email(
            sender_email=sender_email,
            sender_password=sender_password,
            recipient_email=recipient_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            smtp_server=smtp_server,
            smtp_port=smtp_port
        )
        
        if result["status"] == "success":
            logger.info(f"使用 {smtp_server}:{smtp_port} 成功发送邮件")
            return result
        
        logger.warning(f"使用 {smtp_server}:{smtp_port} 发送失败: {result['message']}")
        time.sleep(1)  # 在尝试下一个配置前稍等片刻
    
    return {
        "status": "error",
        "message": "使用所有可用的SMTP配置发送邮件均失败",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import os
    
    sender = os.getenv("EMAIL_SENDER", "example@example.com")
    password = os.getenv("EMAIL_PASSWORD", "")  # 从环境变量加载
    recipient = os.getenv("EMAIL_RECIPIENT", "recipient@example.com")
    
    if not password:
        print("请设置 EMAIL_PASSWORD 环境变量")
        exit(1)
    
    logger.info(f"从 {sender} 发送测试邮件到 {recipient}")
    
    result = try_multiple_smtp_servers(
        sender_email=sender,
        sender_password=password,
        recipient_email=recipient,
        subject="Promora 测试邮件",
        body_text="这是一封来自 Promora 的测试邮件。\n\n此邮件用于测试邮件发送功能。",
        body_html="""
        <html>
        <body>
            <h2>Promora 测试邮件</h2>
            <p>这是一封来自 Promora 的测试邮件。</p>
            <p>此邮件用于测试邮件发送功能。</p>
            <hr>
            <p><em>Promora - AI 驱动的虚拟首席市场官</em></p>
        </body>
        </html>
        """
    )
    
    print(result)
