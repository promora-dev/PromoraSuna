"""
X (Twitter) 账户注册演示脚本

此脚本演示如何使用人类行为模拟进行X平台账户注册，并处理验证挑战。
增加了详细日志记录，以便更好地诊断注册过程中的问题。
"""

import os
import sys
import asyncio
import logging
import json
import random
import string
import traceback
from pathlib import Path
from datetime import datetime

from promora.platform_publisher.test_browser_tool import TestBrowserTool
from promora.platform_publisher.human_registration import HumanRegistration
from promora.platform_publisher.verification_dialog import VerificationDialog
from promora.platform_publisher.models import PlatformAccount, PlatformType

logging.basicConfig(
    level=logging.DEBUG,  # 使用DEBUG级别以获取更多详细信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/tmp/promora_x_registration_debug.log")
    ]
)
logger = logging.getLogger("x_registration_demo")

logging.getLogger("playwright").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

async def handle_verification_challenge(verification_id, verification_code=None):
    """处理验证挑战
    
    Args:
        verification_id: 验证ID
        verification_code: 验证码，如果为None则提示用户输入
        
    Returns:
        是否成功处理验证挑战
    """
    logger.debug(f"处理验证挑战: ID={verification_id}")
    if verification_code is None:
        verification_code = input(f"请输入验证码 (验证ID: {verification_id}): ")
    
    result = {
        "code": verification_code,
        "action": "submit"
    }
    
    logger.debug(f"提交验证结果: {result}")
    success = await VerificationDialog.submit_verification_result(
        verification_id=verification_id,
        result=result
    )
    
    logger.debug(f"验证结果处理状态: {'成功' if success else '失败'}")
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

def trace_method(func):
    async def wrapper(*args, **kwargs):
        logger.debug(f"开始执行: {func.__name__}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"完成执行: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"执行{func.__name__}时出错: {e}")
            logger.error(traceback.format_exc())
            raise
    return wrapper

original_register_x_account = HumanRegistration.register_x_account
HumanRegistration.register_x_account = trace_method(original_register_x_account)

original_human_click = HumanRegistration._human_click
HumanRegistration._human_click = trace_method(original_human_click)

original_human_typing = HumanRegistration._human_typing
HumanRegistration._human_typing = trace_method(original_human_typing)

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
        headless=True,   # 使用无头模式，避免需要XServer
        slow_mo=100,     # 操作之间的延迟（毫秒）
        timeout=60000,   # 默认超时时间（毫秒）
        screenshot_dir=str(debug_dir)
    )
    
    try:
        logger.info("启动浏览器...")
        await browser_tool.start()
        
        initial_screenshot = f"{debug_dir}/initial_browser_{int(datetime.now().timestamp())}.png"
        await browser_tool.screenshot(initial_screenshot)
        logger.debug(f"初始浏览器截图: {initial_screenshot}")
        
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
        else:
            logger.debug(f"使用邮箱: {email_address} ({email_provider})")
        
        human_registration = HumanRegistration(
            browser_tool=browser_tool,
            email_address=email_address,
            email_password=email_password,
            email_provider=email_provider
        )
        
        human_registration.screenshot_dir = str(debug_dir)
        
        browser_tool.timeout = 30000  # 30秒
        
        logger.info(f"开始注册X账户: {username} / {email}")
        
        logger.debug("步骤1: 导航到X注册页面")
        await browser_tool.navigate("https://twitter.com/i/flow/signup")
        await asyncio.sleep(3)  # 等待页面加载
        
        signup_screenshot = f"{debug_dir}/signup_page_{int(datetime.now().timestamp())}.png"
        await browser_tool.screenshot(signup_screenshot)
        logger.debug(f"注册页面截图: {signup_screenshot}")
        
        logger.debug("检查页面上的关键元素...")
        create_account_exists = await browser_tool.element_exists("span:has-text('Create account')")
        logger.debug(f"'Create account'按钮存在: {create_account_exists}")
        
        logger.debug("步骤2: 开始注册过程")
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
            
            final_screenshot = f"{debug_dir}/final_state_{int(datetime.now().timestamp())}.png"
            await browser_tool.screenshot(final_screenshot)
            logger.debug(f"最终页面状态截图: {final_screenshot}")
            
            return None
        
    except Exception as e:
        logger.error(f"演示过程中出错: {e}")
        logger.error(traceback.format_exc())
        
        error_screenshot = f"{debug_dir}/error_state_{int(datetime.now().timestamp())}.png"
        try:
            await browser_tool.screenshot(error_screenshot)
            logger.debug(f"错误状态截图: {error_screenshot}")
        except:
            logger.error("无法截取错误状态截图")
        
        raise
    finally:
        logger.info("关闭浏览器...")
        await browser_tool.close()

if __name__ == "__main__":
    asyncio.run(demo_x_registration())
