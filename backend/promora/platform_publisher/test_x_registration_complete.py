"""
X (Twitter) 账户注册完整测试脚本

此脚本演示完整的X平台账户注册流程，包括处理各种验证挑战和模拟人类行为。
"""

import os
import sys
import asyncio
import logging
import json
import random
import string
import argparse
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/tmp/promora_x_registration_complete.log")
    ]
)
logger = logging.getLogger("x_registration_complete")

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from promora.platform_publisher.test_browser_tool import TestBrowserTool
from promora.platform_publisher.human_registration import HumanRegistration
from promora.platform_publisher.verification_dialog import VerificationDialog
from promora.platform_publisher.models import PlatformAccount, PlatformType
from promora.platform_publisher.email_client import EmailClientFactory

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
    elif verification_data['type'] == 'sms':
        verification_code = input(f"请输入短信验证码 (验证ID: {verification_data['id']}): ")
        await handle_verification_challenge(verification_data['id'], verification_code)
    elif verification_data['type'] == 'security_verification':
        print(f"请完成安全验证，然后按回车键继续...")
        input()
        await handle_verification_challenge(verification_data['id'], "completed")

async def test_x_registration_complete(args):
    """完整测试X账户注册过程
    
    Args:
        args: 命令行参数
    
    Returns:
        注册的账户信息，如果注册失败则返回None
    """
    debug_dir = Path("/tmp/promora_x_registration_complete")
    debug_dir.mkdir(exist_ok=True)
    
    email = args.email
    password = args.password
    username = args.username
    display_name = args.display_name
    
    if not email:
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        email = f"test.{random_str}@promora.ai"
    
    if not password:
        password = ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=12))
    
    if not username:
        username = f"promora_{random.randint(10000, 99999)}"
    
    if not display_name:
        display_name = f"Promora Test {random.randint(100, 999)}"
    
    logger.info(f"开始完整测试X账户注册: {username} / {email}")
    logger.info(f"使用的密码: {password}")
    
    browser_tool = TestBrowserTool(
        headless=not args.show_browser,  # 根据参数决定是否显示浏览器
        slow_mo=args.slow_mo,            # 操作之间的延迟（毫秒）
        timeout=args.timeout,            # 默认超时时间（毫秒）
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
        
        email_address = args.email_address or os.environ.get("EMAIL_ADDRESS")
        email_password = args.email_password or os.environ.get("EMAIL_PASSWORD")
        email_provider = args.email_provider or os.environ.get("EMAIL_PROVIDER", "gmail")
        
        email_client = None
        if email_address and email_password:
            logger.info(f"连接邮箱: {email_address} ({email_provider})")
            try:
                email_client = EmailClientFactory.create_client(
                    email_address=email_address,
                    password=email_password,
                    provider=email_provider
                )
                
                if email_client.connect():
                    logger.info("邮箱连接成功")
                else:
                    logger.warning("邮箱连接失败，将无法自动处理邮箱验证")
                    email_client = None
            except Exception as e:
                logger.error(f"创建邮箱客户端时出错: {e}")
                email_client = None
        else:
            logger.warning("未提供邮箱凭据，将无法自动处理邮箱验证")
        
        human_registration = HumanRegistration(
            browser_tool=browser_tool,
            email_client=email_client,
            email_address=email_address,
            email_password=email_password,
            email_provider=email_provider
        )
        
        human_registration.screenshot_dir = str(debug_dir)
        
        human_registration.min_typing_delay = args.min_typing_delay
        human_registration.max_typing_delay = args.max_typing_delay
        human_registration.min_action_delay = args.min_action_delay
        human_registration.max_action_delay = args.max_action_delay
        
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

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="X账户注册完整测试脚本")
    
    parser.add_argument("--email", help="注册邮箱")
    parser.add_argument("--password", help="注册密码")
    parser.add_argument("--username", help="用户名")
    parser.add_argument("--display-name", help="显示名称")
    
    parser.add_argument("--email-address", help="用于接收验证邮件的邮箱地址")
    parser.add_argument("--email-password", help="邮箱密码")
    parser.add_argument("--email-provider", default="gmail", help="邮箱提供商（默认为gmail）")
    
    parser.add_argument("--show-browser", action="store_true", help="显示浏览器窗口")
    parser.add_argument("--slow-mo", type=int, default=100, help="操作之间的延迟（毫秒）")
    parser.add_argument("--timeout", type=int, default=60000, help="默认超时时间（毫秒）")
    
    parser.add_argument("--min-typing-delay", type=float, default=0.05, help="最小输入延迟（秒）")
    parser.add_argument("--max-typing-delay", type=float, default=0.15, help="最大输入延迟（秒）")
    parser.add_argument("--min-action-delay", type=float, default=0.5, help="最小操作延迟（秒）")
    parser.add_argument("--max-action-delay", type=float, default=2.0, help="最大操作延迟（秒）")
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(test_x_registration_complete(args))
