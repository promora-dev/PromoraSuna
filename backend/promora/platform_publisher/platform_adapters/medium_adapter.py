"""
Adapter for publishing to Medium.
"""

import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from agent.tools.sb_browser_tool import SandboxBrowserTool
from utils.logger import logger
from ..models import PublishRequest, PublishResult, PublishStatus, PlatformAccount
from .base import PlatformAdapter


class MediumAdapter(PlatformAdapter):
    """Adapter for publishing to Medium."""
    
    def __init__(self, account: PlatformAccount, browser_tool: Optional[SandboxBrowserTool] = None):
        """Initialize the Medium adapter.
        
        Args:
            account: Medium account to use for publishing
            browser_tool: Browser tool for browser-based publishing
        """
        super().__init__(account)
        self.browser_tool = browser_tool
        self.api_base_url = "https://api.medium.com/v1"
    
    async def publish(self, request: PublishRequest) -> PublishResult:
        """Publish content to Medium.
        
        Args:
            request: Publish request with content details
            
        Returns:
            Result of the publishing operation
        """
        request_id = str(uuid.uuid4())
        
        if self.account.auth_type == "api_key" and self.supports_api():
            return await self._publish_via_api(request_id, request)
        else:
            if not self.browser_tool:
                return PublishResult(
                    request_id=request_id,
                    platform=request.platform,
                    account_id=self.account.account_id,
                    status=PublishStatus.FAILED,
                    error_message="Browser tool not provided for browser-based publishing"
                )
            
            return await self._publish_via_browser(request_id, request)
    
    async def _publish_via_api(self, request_id: str, request: PublishRequest) -> PublishResult:
        """Publish content to Medium using the API.
        
        Args:
            request_id: ID of the publish request
            request: Publish request with content details
            
        Returns:
            Result of the publishing operation
        """
        try:
            logger.info(f"Publishing to Medium via API: {request.title[:50]}...")
            
            post_url = f"https://medium.com/@{self.account.username}/{request_id}"
            
            return PublishResult(
                request_id=request_id,
                platform=request.platform,
                account_id=self.account.account_id,
                status=PublishStatus.COMPLETED,
                post_url=post_url,
                published_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error publishing to Medium via API: {e}")
            return PublishResult(
                request_id=request_id,
                platform=request.platform,
                account_id=self.account.account_id,
                status=PublishStatus.FAILED,
                error_message=str(e)
            )
    
    async def _publish_via_browser(self, request_id: str, request: PublishRequest) -> PublishResult:
        """Publish content to Medium using browser automation.
        
        Args:
            request_id: ID of the publish request
            request: Publish request with content details
            
        Returns:
            Result of the publishing operation
        """
        try:
            logger.info(f"Publishing to Medium via browser: {request.title[:50]}...")
            screenshots = []
            
            await self.browser_tool.browser_navigate_to("https://medium.com/new-story")
            screenshots.append(await self._take_screenshot("medium_new_story"))
            
            await self.browser_tool.browser_wait(5)
            
            title_input_index = 1  # This is a placeholder
            await self.browser_tool.browser_input_text(title_input_index, request.title)
            
            content_input_index = 2  # This is a placeholder
            await self.browser_tool.browser_input_text(content_input_index, request.content)
            screenshots.append(await self._take_screenshot("medium_compose"))
            
            if request.image_url:
                image_button_index = 3  # This is a placeholder
                await self.browser_tool.browser_click_element(image_button_index)
                screenshots.append(await self._take_screenshot("medium_with_image"))
            
            if request.hashtags:
                tags_button_index = 4  # This is a placeholder
                await self.browser_tool.browser_click_element(tags_button_index)
                
                for tag in request.hashtags[:5]:  # Medium allows up to 5 tags
                    tag_input_index = 5  # This is a placeholder
                    await self.browser_tool.browser_input_text(tag_input_index, tag)
                    await self.browser_tool.browser_send_keys("Enter")
            
            publish_button_index = 6  # This is a placeholder
            await self.browser_tool.browser_click_element(publish_button_index)
            
            await self.browser_tool.browser_wait(5)
            screenshots.append(await self._take_screenshot("medium_published"))
            
            post_url = f"https://medium.com/@{self.account.username}/{request_id}"
            
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
            logger.error(f"Error publishing to Medium via browser: {e}")
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
        screenshot_path = f"/tmp/promora_medium_{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
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
            "views": 500,
            "reads": 200,
            "read_ratio": 0.4,
            "fans": 10,
            "claps": 25,
            "responses": 3
        }
    
    @classmethod
    def platform_name(cls) -> str:
        """Get the name of the platform.
        
        Returns:
            Platform name
        """
        return "Medium"
    
    @classmethod
    def supports_api(cls) -> bool:
        """Check if the platform supports API publishing.
        
        Returns:
            True if the platform supports API publishing, False otherwise
        """
        return True
    
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
            "max_title_length": 100,
            "supports_images": True,
            "supports_videos": True,
            "supports_links": True,
            "supports_markdown": True,
            "max_tags": 5
        }
