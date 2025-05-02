"""
模拟邮件发送模块

由于网络连接限制，此模块提供模拟邮件发送功能，用于测试目的。
"""

import logging
import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MOCK_EMAIL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_emails")
os.makedirs(MOCK_EMAIL_DIR, exist_ok=True)

def send_mock_email(
    sender_email: str,
    sender_password: str,
    recipient_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    模拟发送邮件并将其保存到本地文件
    
    Args:
        sender_email: 发件人邮箱
        sender_password: 发件人密码（不会被存储）
        recipient_email: 收件人邮箱
        subject: 邮件主题
        body_text: 纯文本邮件内容
        body_html: HTML邮件内容（可选）
        cc: 抄送收件人列表（可选）
        bcc: 密送收件人列表（可选）
        
    Returns:
        包含状态和消息的字典
    """
    logger.info(f"模拟从 {sender_email} 发送邮件到 {recipient_email}")
    
    time.sleep(1.5)
    
    timestamp = datetime.now().isoformat()
    email_id = f"{int(time.time())}_{hash(sender_email + recipient_email + timestamp) % 10000:04d}"
    
    email_data = {
        "id": email_id,
        "sender": sender_email,
        "recipient": recipient_email,
        "cc": cc or [],
        "bcc": bcc or [],
        "subject": subject,
        "body_text": body_text,
        "body_html": body_html,
        "timestamp": timestamp,
        "status": "sent"
    }
    
    email_file = os.path.join(MOCK_EMAIL_DIR, f"email_{email_id}.json")
    try:
        with open(email_file, 'w', encoding='utf-8') as f:
            json.dump(email_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"模拟邮件已保存到: {email_file}")
        
        return {
            "status": "success",
            "message": f"邮件成功发送到 {recipient_email}（模拟）",
            "email_id": email_id,
            "timestamp": timestamp,
            "file_path": email_file
        }
    except Exception as e:
        error_message = f"保存模拟邮件失败: {str(e)}"
        logger.error(error_message)
        return {
            "status": "error",
            "message": error_message,
            "error": str(e),
            "timestamp": timestamp
        }

def get_mock_email(email_id: str) -> Optional[Dict[str, Any]]:
    """
    获取模拟邮件数据
    
    Args:
        email_id: 邮件ID
        
    Returns:
        邮件数据字典，如果不存在则返回None
    """
    email_file = os.path.join(MOCK_EMAIL_DIR, f"email_{email_id}.json")
    
    if not os.path.exists(email_file):
        logger.warning(f"邮件不存在: {email_id}")
        return None
    
    try:
        with open(email_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取邮件失败: {str(e)}")
        return None

def list_mock_emails(sender: Optional[str] = None, recipient: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    列出所有模拟邮件
    
    Args:
        sender: 过滤发件人（可选）
        recipient: 过滤收件人（可选）
        
    Returns:
        邮件数据字典列表
    """
    emails = []
    
    for filename in os.listdir(MOCK_EMAIL_DIR):
        if not filename.startswith("email_") or not filename.endswith(".json"):
            continue
        
        try:
            with open(os.path.join(MOCK_EMAIL_DIR, filename), 'r', encoding='utf-8') as f:
                email_data = json.load(f)
                
                if sender and email_data.get("sender") != sender:
                    continue
                
                if recipient and email_data.get("recipient") != recipient:
                    continue
                
                emails.append(email_data)
        except Exception as e:
            logger.error(f"读取邮件失败 {filename}: {str(e)}")
    
    emails.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return emails

if __name__ == "__main__":
    import os
    
    sender = os.getenv("EMAIL_SENDER", "example@example.com")
    password = os.getenv("EMAIL_PASSWORD", "")  # 从环境变量加载
    recipient = os.getenv("EMAIL_RECIPIENT", "recipient@example.com")
    
    if not password:
        print("请设置 EMAIL_PASSWORD 环境变量")
        exit(1)
    
    logger.info(f"从 {sender} 发送测试邮件到 {recipient}")
    
    result = send_mock_email(
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
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    all_emails = list_mock_emails()
    print(f"\n共找到 {len(all_emails)} 封模拟邮件:")
    for email in all_emails:
        print(f"ID: {email['id']}, 发件人: {email['sender']}, 收件人: {email['recipient']}, 主题: {email['subject']}")
