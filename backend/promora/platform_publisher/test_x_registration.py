"""
X (Twitter) 账户注册测试脚本

此脚本用于测试使用人类行为模拟进行X平台账户注册，并处理验证挑战。
"""

import os
import asyncio
import logging
import json
import random
import string
from pathlib import Path
from datetime import datetime

from .test_browser_tool import TestBrowserTool
from .human_registration import HumanRegistration
from .verification_dialog import VerificationDialog
from .models import PlatformAccount, PlatformType

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("x_registration_test")

async def notification_callback(message, verification_data):
    """验证通知回调函数
    
    Args:
        message: 通知消息
        verification_data: 验证数据
    """
    logger.info(f"需要验证: {message}")
    logger.info(f"验证ID: {verification_data['id']}")
    logger.info(f"验证类型: {verification_data['type']}")
    logger.info(f"验证详情: {verification_data['details']}")
    
    if verification_data.get('screenshot'):
        logger.info(f"验证截图: {verification_data['screenshot']}")

async def test_x_registration(email=None, password=None, username=None, display_name=None):
    """测试X账户注册
    
    Args:
        email: 注册邮箱，如果为None则生成随机邮箱
        password: 注册密码，如果为None则生成随机密码
        username: 用户名，如果为None则生成随机用户名
        display_name: 显示名称，如果为None则使用默认值
        
    Returns:
        注册的账户信息，如果注册失败则返回None
    """
    debug_dir = Path("/tmp/promora_x_registration")
    debug_dir.mkdir(exist_ok=True)
    
    if not email:
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        email = f"test.{random_str}@promora.ai"
    
    if not password:
        password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=12))
    
    if not username:
        username = f"promora_{random.randint(10000, 99999)}"
    
    if not display_name:
        display_name = f"Promora Test {random.randint(100, 999)}"
    
    logger.info(f"开始测试X账户注册: {username} / {email}")
    
    browser_tool = TestBrowserTool(
        headless=True,   # 使用无头模式，避免需要XServer
        slow_mo=50,      # 操作之间的延迟（毫秒）
        timeout=60000,   # 默认超时时间（毫秒）
        screenshot_dir=str(debug_dir)
    )
    
    try:
        logger.info("启动浏览器...")
        await browser_tool.start()
        
        verification_dialog = VerificationDialog(
            platform="x",
            account_id=username,
            verification_dir=str(debug_dir),
            notification_callback=notification_callback
        )
        
        email_address = os.environ.get("EMAIL_ADDRESS")
        email_password = os.environ.get("EMAIL_PASSWORD")
        email_provider = os.environ.get("EMAIL_PROVIDER", "gmail")
        
        human_registration = HumanRegistration(
            browser_tool=browser_tool,
            email_address=email_address,
            email_password=email_password,
            email_provider=email_provider
        )
        
        human_registration.screenshot_dir = str(debug_dir)
        
        logger.info(f"开始注册X账户: {username} / {email}")
        account = await human_registration.register_x_account(
            username=username,
            email=email,
            password=password,
            display_name=display_name
        )
        
        if account:
            logger.info(f"X账户注册成功: {account.username}")
            
            account_file = debug_dir / f"x_account_{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            with open(account_file, "w", encoding="utf-8") as f:
                json.dump(account.dict(), f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"账户信息已保存到: {account_file}")
            
            return account
        else:
            logger.warning("X账户注册失败")
            return None
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        raise
    finally:
        logger.info("关闭浏览器...")
        await browser_tool.close()

async def handle_verification_challenge(verification_id, verification_code=None):
    """处理验证挑战
    
    Args:
        verification_id: 验证ID
        verification_code: 验证码，如果为None则提示用户输入
        
    Returns:
        是否成功处理验证挑战
    """
    if verification_code is None:
        verification_code = input(f"请输入验证码 (验证ID: {verification_id}): ")
    
    result = {
        "code": verification_code,
        "action": "submit"
    }
    
    success = await VerificationDialog.submit_verification_result(
        verification_id=verification_id,
        result=result
    )
    
    return success

if __name__ == "__main__":
    asyncio.run(test_x_registration())
