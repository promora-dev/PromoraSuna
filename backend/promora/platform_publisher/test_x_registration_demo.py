"""
X (Twitter) 账户注册演示脚本

此脚本演示如何使用人类行为模拟进行X平台账户注册，并处理验证挑战。
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
logger = logging.getLogger("x_registration_demo")

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
    
    if verification_data['type'] == 'email':
        verification_code = input(f"请输入邮箱验证码 (验证ID: {verification_data['id']}): ")
        await handle_verification_challenge(verification_data['id'], verification_code)
    elif verification_data['type'] == 'captcha':
        verification_code = input(f"请输入图形验证码 (验证ID: {verification_data['id']}): ")
        await handle_verification_challenge(verification_data['id'], verification_code)

async def demo_x_registration():
    """演示X账户注册过程"""
    debug_dir = Path("/tmp/promora_x_registration_demo")
    debug_dir.mkdir(exist_ok=True)
    
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    email = f"test.{random_str}@promora.ai"
    password = ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=12))
    username = f"promora_{random.randint(10000, 99999)}"
    display_name = f"Promora Test {random.randint(100, 999)}"
    
    logger.info(f"开始演示X账户注册: {username} / {email}")
    logger.info(f"生成的随机密码: {password}")
    
    browser_tool = TestBrowserTool(
        headless=False,  # 使用有头模式，便于观察
        slow_mo=100,     # 操作之间的延迟（毫秒）
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
        
        if not email_address or not email_password:
            logger.warning("未设置邮箱凭据环境变量，将无法自动处理邮箱验证")
            logger.info("请设置以下环境变量:")
            logger.info("  EMAIL_ADDRESS: 用于接收验证邮件的邮箱地址")
            logger.info("  EMAIL_PASSWORD: 邮箱密码")
            logger.info("  EMAIL_PROVIDER: 邮箱提供商（默认为gmail）")
        
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
        logger.error(f"演示过程中出错: {e}")
        raise
    finally:
        logger.info("关闭浏览器...")
        await browser_tool.close()

if __name__ == "__main__":
    asyncio.run(demo_x_registration())
