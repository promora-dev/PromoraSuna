"""
交互式LLM引导的X账户注册测试脚本

此脚本演示如何使用交互式LLM引导系统进行X平台账户注册，
通过LLM分析截图并提供操作建议，实现更智能的注册流程。
"""

import os
import sys
import asyncio
import logging
import json
import random
import string
import traceback
import argparse
from pathlib import Path
from datetime import datetime

from promora.platform_publisher.test_browser_tool import TestBrowserTool
from promora.platform_publisher.interactive_registration import InteractiveRegistration
from promora.platform_publisher.verification_dialog import VerificationDialog
from promora.platform_publisher.models import PlatformAccount, PlatformType

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/tmp/promora_interactive_x_registration_debug.log")
    ]
)
logger = logging.getLogger("interactive_x_registration")

logging.getLogger("playwright").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

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

async def test_interactive_x_registration(args):
    """测试交互式LLM引导的X账户注册
    
    Args:
        args: 命令行参数
    
    Returns:
        注册成功的账户信息，失败则返回None
    """
    debug_dir = Path("/tmp/promora_interactive_x_registration")
    debug_dir.mkdir(exist_ok=True)
    
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    email = args.email or f"test.{random_str}@promora.ai"
    password = args.password or ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=12))
    username = args.username or "PromoraAI"  # 默认使用指定的用户名
    display_name = args.display_name or f"Promora AI {random.randint(100, 999)}"
    
    logger.info(f"开始测试交互式LLM引导的X账户注册: {username} / {email}")
    logger.info(f"使用的密码: {password}")
    
    browser_tool = TestBrowserTool(
        headless=not args.show_browser,
        slow_mo=args.slow_mo,
        timeout=args.timeout,
        screenshot_dir=str(debug_dir)
    )
    
    try:
        logger.info("启动浏览器...")
        await browser_tool.start()
        
        initial_screenshot = f"{debug_dir}/initial_browser_{int(datetime.now().timestamp())}.png"
        await browser_tool.screenshot(initial_screenshot)
        logger.debug(f"初始浏览器截图: {initial_screenshot}")
        
        email_address = args.email_address or os.environ.get("EMAIL_ADDRESS")
        email_password = args.email_password or os.environ.get("EMAIL_PASSWORD")
        email_provider = args.email_provider or os.environ.get("EMAIL_PROVIDER", "gmail")
        
        if not email_address or not email_password:
            logger.warning("未设置邮箱凭据，将无法自动处理邮箱验证")
            logger.info("请设置以下环境变量或通过命令行参数提供:")
            logger.info("  EMAIL_ADDRESS: 用于接收验证邮件的邮箱地址")
            logger.info("  EMAIL_PASSWORD: 邮箱密码")
            logger.info("  EMAIL_PROVIDER: 邮箱提供商（默认为gmail）")
        else:
            logger.debug(f"使用邮箱: {email_address} ({email_provider})")
        
        api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("未设置OpenAI API密钥，将无法使用LLM引导功能")
            logger.info("请设置OPENAI_API_KEY环境变量或通过--api-key参数提供")
            return None
        
        interactive_registration = InteractiveRegistration(
            browser_tool=browser_tool,
            email_address=email_address,
            email_password=email_password,
            email_provider=email_provider,
            api_key=api_key,
            verification_callback=notification_callback
        )
        
        interactive_registration.screenshot_dir = str(debug_dir)
        
        logger.info(f"开始注册X账户: {username} / {email}")
        
        account = await interactive_registration.register_x_account(
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
        logger.error(f"测试过程中出错: {e}")
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

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="交互式LLM引导的X账户注册测试")
    
    parser.add_argument("--username", help="X用户名", default="PromoraAI")
    parser.add_argument("--email", help="注册邮箱")
    parser.add_argument("--password", help="账户密码")
    parser.add_argument("--display-name", help="显示名称")
    
    parser.add_argument("--email-address", help="用于接收验证码的邮箱地址")
    parser.add_argument("--email-password", help="邮箱密码")
    parser.add_argument("--email-provider", help="邮箱提供商", default="gmail")
    
    parser.add_argument("--api-key", help="OpenAI API密钥")
    
    parser.add_argument("--show-browser", action="store_true", help="显示浏览器窗口")
    parser.add_argument("--slow-mo", type=int, default=100, help="操作之间的延迟（毫秒）")
    parser.add_argument("--timeout", type=int, default=60000, help="默认超时时间（毫秒）")
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(test_interactive_x_registration(args))
