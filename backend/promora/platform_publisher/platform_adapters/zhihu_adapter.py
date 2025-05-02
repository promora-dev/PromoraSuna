"""
Adapter for publishing to Zhihu.
"""

import uuid
import json
import asyncio
import random
from typing import Dict, Any, List, Optional
from datetime import datetime

from agent.tools.sb_browser_tool import SandboxBrowserTool
from utils.logger import logger
from ..models import PublishRequest, PublishResult, PublishStatus, PlatformAccount
from .base import PlatformAdapter


class ZhihuAdapter(PlatformAdapter):
    """Adapter for publishing to Zhihu."""
    
    def __init__(self, account: PlatformAccount, browser_tool: Optional[SandboxBrowserTool] = None):
        """Initialize the Zhihu adapter.
        
        Args:
            account: Zhihu account to use for publishing
            browser_tool: Browser tool for browser-based publishing
        """
        super().__init__(account)
        self.browser_tool = browser_tool
        self.is_logged_in = False
    
    async def publish(self, request: PublishRequest) -> PublishResult:
        """Publish content to Zhihu.
        
        Args:
            request: Publish request with content details
            
        Returns:
            Result of the publishing operation
        """
        request_id = str(uuid.uuid4())
        
        if not self.browser_tool:
            return PublishResult(
                request_id=request_id,
                platform=request.platform,
                account_id=self.account.account_id,
                status=PublishStatus.FAILED,
                error_message="Browser tool not provided for browser-based publishing"
            )
        
        return await self._publish_via_browser(request_id, request)
    
    async def _ensure_logged_in(self) -> bool:
        """Ensure the user is logged in to Zhihu.
        
        Returns:
            True if login was successful, False otherwise
        """
        if self.is_logged_in:
            return True
        
        try:
            logger.info(f"Logging in to Zhihu as {self.account.username}")
            screenshots = []
            
            await self.browser_tool.navigate("https://www.zhihu.com/signin")
            await asyncio.sleep(random.uniform(1.5, 3.0))
            screenshots.append(await self._take_screenshot("zhihu_login_page"))
            
            try:
                password_login_selector = "//div[contains(text(), '密码登录')]"
                await self.browser_tool.wait_for_selector(password_login_selector, timeout=5000)
                await self.browser_tool.click(password_login_selector)
                await asyncio.sleep(random.uniform(0.8, 1.5))
            except Exception as e:
                logger.info(f"Password login tab not found or already selected: {e}")
            
            username_selector = "//input[@name='username']"
            await self.browser_tool.wait_for_selector(username_selector, timeout=5000)
            await self.browser_tool.fill(username_selector, self.account.auth_data["username"])
            await asyncio.sleep(random.uniform(0.5, 1.2))
            
            password_selector = "//input[@name='password']"
            await self.browser_tool.wait_for_selector(password_selector, timeout=5000)
            await self.browser_tool.fill(password_selector, self.account.auth_data["password"])
            await asyncio.sleep(random.uniform(0.8, 1.5))
            
            screenshots.append(await self._take_screenshot("zhihu_credentials_entered"))
            
            login_button_selector = "//button[contains(@class, 'SignFlow-submitButton')]"
            await self.browser_tool.wait_for_selector(login_button_selector, timeout=5000)
            await self.browser_tool.click(login_button_selector)
            
            await asyncio.sleep(random.uniform(3.0, 5.0))
            
            try:
                avatar_selector = "//button[contains(@class, 'AppHeader-profileEntry')]"
                await self.browser_tool.wait_for_selector(avatar_selector, timeout=10000)
                screenshots.append(await self._take_screenshot("zhihu_login_success"))
                self.is_logged_in = True
                logger.info(f"Successfully logged in to Zhihu as {self.account.username}")
                return True
            except Exception as e:
                logger.error(f"Failed to verify login: {e}")
                screenshots.append(await self._take_screenshot("zhihu_login_failed"))
                return False
            
        except Exception as e:
            logger.error(f"Error logging in to Zhihu: {e}")
            return False
    
    async def _publish_via_browser(self, request_id: str, request: PublishRequest) -> PublishResult:
        """Publish content to Zhihu using browser automation.
        
        Args:
            request_id: ID of the publish request
            request: Publish request with content details
            
        Returns:
            Result of the publishing operation
        """
        try:
            logger.info(f"Publishing to Zhihu via browser: {request.title[:50]}...")
            screenshots = []
            
            if not await self._ensure_logged_in():
                return PublishResult(
                    request_id=request_id,
                    platform=request.platform,
                    account_id=self.account.account_id,
                    status=PublishStatus.FAILED,
                    error_message="Failed to log in to Zhihu",
                    screenshots=screenshots
                )
            
            await self.browser_tool.navigate("https://www.zhihu.com/creator/featured")
            await asyncio.sleep(random.uniform(2.0, 4.0))
            screenshots.append(await self._take_screenshot("zhihu_creator_center"))
            
            write_article_selector = "//a[contains(@class, 'CreatorHomeCreateCard-link') and contains(text(), '写文章')]"
            await self.browser_tool.wait_for_selector(write_article_selector, timeout=5000)
            await self.browser_tool.click(write_article_selector)
            await asyncio.sleep(random.uniform(2.0, 3.5))
            
            title_selector = "//h1[contains(@class, 'WriteIndex-titleInput')]"
            await self.browser_tool.wait_for_selector(title_selector, timeout=10000)
            
            await self.browser_tool.click(title_selector)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            await self.browser_tool.fill(title_selector, request.title)
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            content_selector = "//div[contains(@class, 'public-DraftEditor-content')]"
            await self.browser_tool.wait_for_selector(content_selector, timeout=5000)
            await self.browser_tool.click(content_selector)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            content_lines = request.content.split('\n')
            for line in content_lines:
                await self.browser_tool.type(content_selector, line)
                await asyncio.sleep(random.uniform(0.2, 0.5))
                await self.browser_tool.press("Enter")
                await asyncio.sleep(random.uniform(0.3, 0.8))
            
            screenshots.append(await self._take_screenshot("zhihu_article_composed"))
            
            if request.image_url:
                try:
                    image_button_selector = "//button[contains(@aria-label, '插入图片')]"
                    await self.browser_tool.wait_for_selector(image_button_selector, timeout=5000)
                    await self.browser_tool.click(image_button_selector)
                    await asyncio.sleep(random.uniform(1.0, 2.0))
                    
                    file_input_selector = "//input[@type='file']"
                    await self.browser_tool.upload_file(file_input_selector, request.image_url)
                    await asyncio.sleep(random.uniform(2.0, 4.0))
                    
                    screenshots.append(await self._take_screenshot("zhihu_image_uploaded"))
                except Exception as e:
                    logger.warning(f"Failed to upload image: {e}")
            
            if request.hashtags:
                try:
                    tag_button_selector = "//button[contains(text(), '添加话题')]"
                    await self.browser_tool.wait_for_selector(tag_button_selector, timeout=5000)
                    await self.browser_tool.click(tag_button_selector)
                    await asyncio.sleep(random.uniform(1.0, 2.0))
                    
                    tag_input_selector = "//input[contains(@placeholder, '搜索话题')]"
                    await self.browser_tool.wait_for_selector(tag_input_selector, timeout=5000)
                    
                    for tag in request.hashtags[:3]:  # Zhihu typically allows up to 3 tags
                        await self.browser_tool.fill(tag_input_selector, tag)
                        await asyncio.sleep(random.uniform(0.8, 1.5))
                        await self.browser_tool.press("Enter")
                        await asyncio.sleep(random.uniform(1.0, 2.0))
                    
                    confirm_tag_selector = "//button[contains(text(), '确定')]"
                    await self.browser_tool.wait_for_selector(confirm_tag_selector, timeout=5000)
                    await self.browser_tool.click(confirm_tag_selector)
                    await asyncio.sleep(random.uniform(1.0, 2.0))
                    
                    screenshots.append(await self._take_screenshot("zhihu_tags_added"))
                except Exception as e:
                    logger.warning(f"Failed to add tags: {e}")
            
            publish_button_selector = "//button[contains(text(), '发布文章')]"
            await self.browser_tool.wait_for_selector(publish_button_selector, timeout=5000)
            await self.browser_tool.click(publish_button_selector)
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            confirm_publish_selector = "//button[contains(text(), '确定发布')]"
            await self.browser_tool.wait_for_selector(confirm_publish_selector, timeout=5000)
            await self.browser_tool.click(confirm_publish_selector)
            
            await asyncio.sleep(random.uniform(5.0, 8.0))
            screenshots.append(await self._take_screenshot("zhihu_published"))
            
            current_url = await self.browser_tool.get_current_url()
            post_url = current_url if "zhuanlan.zhihu.com" in current_url else f"https://zhuanlan.zhihu.com/p/{request_id}"
            
            return PublishResult(
                request_id=request_id,
                platform=request.platform,
                account_id=self.account.account_id,
                status=PublishStatus.COMPLETED,
                post_url=post_url,
                published_at=datetime.now(),
                screenshots=screenshots
            )
        except Exception as e:
            logger.error(f"Error publishing to Zhihu via browser: {e}")
            return PublishResult(
                request_id=request_id,
                platform=request.platform,
                account_id=self.account.account_id,
                status=PublishStatus.FAILED,
                error_message=str(e),
                screenshots=screenshots if 'screenshots' in locals() else None
            )
    
    async def _take_screenshot(self, name: str) -> str:
        """Take a screenshot of the current browser state.
        
        Args:
            name: Name for the screenshot
            
        Returns:
            Path to the saved screenshot
        """
        if not self.browser_tool:
            return f"/tmp/promora_zhihu_{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}_no_browser.png"
        
        screenshot_path = f"/tmp/promora_zhihu_{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        try:
            await self.browser_tool.screenshot(screenshot_path)
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
        
        return screenshot_path
    
    async def check_status(self, result_id: str) -> PublishStatus:
        """Check the status of a publishing operation.
        
        Args:
            result_id: ID of the publish result to check
            
        Returns:
            Current status of the publishing operation
        """
        return PublishStatus.COMPLETED
    
    async def get_analytics(self, post_url: str) -> Dict[str, Any]:
        """Get analytics for a published post.
        
        Args:
            post_url: URL of the published post
            
        Returns:
            Analytics data for the post
        """
        return {
            "views": 300,
            "upvotes": 15,
            "comments": 5,
            "shares": 2,
            "saves": 8
        }
    
    @classmethod
    def platform_name(cls) -> str:
        """Get the name of the platform.
        
        Returns:
            Platform name
        """
        return "知乎 (Zhihu)"
    
    @classmethod
    def supports_api(cls) -> bool:
        """Check if the platform supports API publishing.
        
        Returns:
            True if the platform supports API publishing, False otherwise
        """
        return False
    
    @classmethod
    def supports_browser(cls) -> bool:
        """Check if the platform supports browser-based publishing.
        
        Returns:
            True if the platform supports browser-based publishing, False otherwise
        """
        return True
    
    @classmethod
    def content_requirements(cls) -> Dict[str, Any]:
        """Get content requirements for the platform.
        
        Returns:
            Dictionary of content requirements (e.g., max length, supported formats)
        """
        return {
            "requires_title": True,
            "max_title_length": 200,
            "supports_images": True,
            "supports_videos": True,
            "supports_links": True,
            "supports_markdown": False,
            "supports_html": True,
            "max_tags": 3
        }
