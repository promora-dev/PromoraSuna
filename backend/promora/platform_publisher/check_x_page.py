"""
简单脚本，用于检查X注册页面的结构并截图。
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime

from promora.platform_publisher.test_browser_tool import TestBrowserTool

async def check_x_registration_page():
    """检查X注册页面的结构并截图"""
    debug_dir = Path("/tmp/promora_x_check")
    debug_dir.mkdir(exist_ok=True)
    
    browser_tool = TestBrowserTool(
        headless=True,
        slow_mo=50,
        timeout=60000,
        screenshot_dir=str(debug_dir)
    )
    
    try:
        print("启动浏览器...")
        await browser_tool.start()
        
        print("导航到X注册页面...")
        await browser_tool.navigate("https://twitter.com/i/flow/signup")
        await asyncio.sleep(3)  # 等待页面加载
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        screenshot_path = str(debug_dir / f"x_signup_{timestamp}.png")
        await browser_tool.screenshot(screenshot_path)
        print(f"页面截图已保存到: {screenshot_path}")
        
        print("检查页面元素...")
        
        selectors = [
            "div[role='button']:has-text('Create account')",
            "div[role='button']:has-text('创建账号')",
            "div[role='button']",
            "span:has-text('Create account')",
            "span:has-text('创建账号')"
        ]
        
        for selector in selectors:
            exists = await browser_tool.element_exists(selector)
            print(f"选择器 '{selector}' 存在: {exists}")
            
            if exists:
                element = await browser_tool.find_element(selector)
                if element:
                    element_screenshot = str(debug_dir / f"element_{selector.replace(':', '_').replace('[', '_').replace(']', '_')}_{timestamp}.png")
                    await browser_tool.screenshot_element(element, element_screenshot)
                    print(f"元素截图已保存到: {element_screenshot}")
        
        html = await browser_tool.evaluate("document.body.innerHTML")
        html_path = str(debug_dir / f"x_signup_html_{timestamp}.txt")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"页面HTML已保存到: {html_path}")
        
    except Exception as e:
        print(f"检查过程中出错: {e}")
    finally:
        print("关闭浏览器...")
        await browser_tool.close()

if __name__ == "__main__":
    asyncio.run(check_x_registration_page())
