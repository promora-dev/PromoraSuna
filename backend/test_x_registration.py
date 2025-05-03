"""
测试交互式LLM引导的X账户注册脚本

此脚本用于测试交互式LLM引导系统进行X平台账户注册的功能，
通过调用test_interactive_x_registration模块进行测试。
使用真实邮箱凭据进行测试。
"""

import os
import sys
import asyncio
import traceback
import logging
from pathlib import Path
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from promora.platform_publisher.test_browser_tool import TestBrowserTool
from promora.platform_publisher.interactive_registration import InteractiveRegistration
from promora.platform_publisher.models import PlatformAccount, PlatformType

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("x_registration_test")

async def main():
    """主函数"""
    username = os.environ.get("X_USERNAME", "TestUser")
    email = os.environ.get("X_EMAIL", "")
    password = os.environ.get("X_PASSWORD", "")
    display_name = os.environ.get("X_DISPLAY_NAME", "Test User")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    show_browser = False  # 使用无头模式，避免XServer问题
    
    debug_dir = Path("/tmp/promora_x_registration_test")
    debug_dir.mkdir(exist_ok=True)
    
    logger.info(f"开始测试X账户注册流程，用户名: {username}")
    logger.info(f"使用邮箱: {email}")
    logger.info(f"调试信息将保存到: {debug_dir}")
    
    if not api_key:
        logger.error("未设置OPENAI_API_KEY环境变量，无法继续测试")
        return 1
    
    browser_tool = TestBrowserTool(
        headless=not show_browser,
        slow_mo=200,
        timeout=60000,
        screenshot_dir=str(debug_dir)
    )
    
    try:
        logger.info("启动浏览器...")
        await browser_tool.start()
        
        registration = InteractiveRegistration(
            browser_tool=browser_tool,
            api_key=api_key,
            email_address=email,
            email_password=password,
            verification_callback=None
        )
        
        account = await registration.register_x_account(
            username=username,
            email=email,
            password=password,
            display_name=display_name
        )
        
        if account:
            logger.info(f"✅ 测试成功! X账户 {account.username} 注册完成")
            return 0
        else:
            logger.info("❌ 测试失败! 未能完成X账户注册")
            return 1
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        logger.error(traceback.format_exc())
        return 1
    finally:
        logger.info("关闭浏览器...")
        await browser_tool.close()

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
