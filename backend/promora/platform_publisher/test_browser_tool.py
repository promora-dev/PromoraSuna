"""
简化的浏览器工具，用于测试目的。

此模块提供了一个简化的浏览器工具，用于测试知乎适配器。
"""

import os
import asyncio
import random
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page, Playwright

class TestBrowserTool:
    """用于测试的简化浏览器工具"""
    
    def __init__(self, headless=False, slow_mo=50, timeout=60000, screenshot_dir=None):
        """初始化浏览器工具
        
        Args:
            headless: 是否以无头模式运行浏览器
            slow_mo: 操作之间的延迟（毫秒）
            timeout: 默认超时时间（毫秒）
            screenshot_dir: 截图保存目录
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.timeout = timeout
        self.playwright = None
        self.browser = None
        self.page = None
        self.context = None
        self.screenshot_dir = Path(screenshot_dir) if screenshot_dir else Path("/tmp/promora_screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def start(self):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        )
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout)
        
        await self.page.route("**/*", self._add_random_delay)
    
    async def _add_random_delay(self, route):
        """添加随机延迟以模拟人类行为"""
        await asyncio.sleep(random.uniform(0.1, 0.5))
        await route.continue_()
    
    async def close(self):
        """关闭浏览器"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def navigate(self, url):
        """导航到指定URL
        
        Args:
            url: 要导航到的URL
        """
        await self.page.goto(url, wait_until="networkidle")
        return {"url": url, "title": await self.page.title()}
    
    async def wait_for_selector(self, selector, timeout=None):
        """等待选择器出现
        
        Args:
            selector: 要等待的选择器
            timeout: 超时时间（毫秒）
        """
        timeout = timeout or self.timeout
        await self.page.wait_for_selector(selector, timeout=timeout)
    
    async def click(self, selector):
        """点击元素
        
        Args:
            selector: 要点击的元素选择器
        """
        await self.page.click(selector)
    
    async def fill(self, selector, text):
        """填充文本
        
        Args:
            selector: 要填充的元素选择器
            text: 要填充的文本
        """
        await self.page.fill(selector, text)
    
    async def type(self, selector, text, delay=None):
        """模拟人类输入文本
        
        Args:
            selector: 要输入的元素选择器
            text: 要输入的文本
            delay: 每个字符之间的延迟（毫秒）
        """
        delay = delay or random.uniform(50, 150)
        await self.page.type(selector, text, delay=delay)
    
    async def press(self, key):
        """按下键盘按键
        
        Args:
            key: 要按下的键
        """
        await self.page.keyboard.press(key)
    
    async def get_current_url(self):
        """获取当前URL
        
        Returns:
            当前URL
        """
        return self.page.url
    
    async def screenshot(self, path=None):
        """截取屏幕截图
        
        Args:
            path: 截图保存路径
            
        Returns:
            截图保存路径
        """
        if not path:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            path = str(self.screenshot_dir / f"screenshot_{timestamp}.png")
        
        await self.page.screenshot(path=path)
        return path
    
    async def upload_file(self, selector, file_path):
        """上传文件
        
        Args:
            selector: 文件输入元素选择器
            file_path: 要上传的文件路径
        """
        await self.page.set_input_files(selector, file_path)
    
    async def evaluate(self, script):
        """执行JavaScript
        
        Args:
            script: 要执行的JavaScript代码
            
        Returns:
            执行结果
        """
        return await self.page.evaluate(script)
        
    async def is_visible(self, selector, timeout=None):
        """检查元素是否可见
        
        Args:
            selector: 要检查的元素选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            如果元素可见则返回True，否则返回False
        """
        timeout = timeout or self.timeout
        try:
            await self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            return True
        except Exception:
            return False
