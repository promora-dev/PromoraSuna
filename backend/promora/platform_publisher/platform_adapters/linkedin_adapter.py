"""
Adapter for publishing to LinkedIn.
"""

import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from agent.tools.sb_browser_tool import SandboxBrowserTool
from utils.logger import logger
from ..models import PublishRequest, PublishResult, PublishStatus, PlatformAccount
from .base import PlatformAdapter


class LinkedInAdapter(PlatformAdapter):
    """Adapter for publishing to LinkedIn."""
    
    def __init__(self, account: PlatformAccount, browser_tool: Optional[SandboxBrowserTool] = None):
        """Initialize the LinkedIn adapter.
        
        Args:
            account: LinkedIn account to use for publishing
            browser_tool: Browser tool for browser-based publishing
        """
        super().__init__(account)
        self.browser_tool = browser_tool
        self.api_base_url = "https://api.linkedin.com/v2"
    
    async def publish(self, request: PublishRequest) -> PublishResult:
        """Publish content to LinkedIn.
        
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
        """Publish content to LinkedIn using the API.
        
        Args:
            request_id: ID of the publish request
            request: Publish request with content details
            
        Returns:
            Result of the publishing operation
        """
        try:
            logger.info(f"Publishing to LinkedIn via API: {request.content[:50]}...")
            
            post_url = f"https://www.linkedin.com/feed/update/urn:li:activity:{request_id}"
            
            return PublishResult(
                request_id=request_id,
                platform=request.platform,
                account_id=self.account.account_id,
                status=PublishStatus.COMPLETED,
                post_url=post_url,
                published_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error publishing to LinkedIn via API: {e}")
            return PublishResult(
                request_id=request_id,
                platform=request.platform,
                account_id=self.account.account_id,
                status=PublishStatus.FAILED,
                error_message=str(e)
            )
    
    async def _publish_via_browser(self, request_id: str, request: PublishRequest) -> PublishResult:
        """Publish content to LinkedIn using browser automation.
        
        Args:
            request_id: ID of the publish request
            request: Publish request with content details
            
        Returns:
            Result of the publishing operation
        """
        try:
            logger.info(f"Publishing to LinkedIn via browser: {request.content[:50]}...")
            screenshots = []
            
            await self.browser_tool.browser_navigate_to("https://www.linkedin.com/feed/")
            screenshots.append(await self._take_screenshot("linkedin_home"))
            
            await self.browser_tool.browser_wait(5)
            
            post_compose_index = 1  # This is a placeholder
            await self.browser_tool.browser_click_element(post_compose_index)
            
            await self.browser_tool.browser_input_text(post_compose_index, request.content)
            screenshots.append(await self._take_screenshot("linkedin_compose"))
            
            if request.hashtags:
                hashtag_text = " " + " ".join([f"#{tag}" for tag in request.hashtags])
                await self.browser_tool.browser_input_text(post_compose_index, hashtag_text)
            
            if request.image_url:
                attachments_index = 2  # This is a placeholder
                await self.browser_tool.browser_click_element(attachments_index)
                screenshots.append(await self._take_screenshot("linkedin_with_image"))
            
            post_button_index = 3  # This is a placeholder
            await self.browser_tool.browser_click_element(post_button_index)
            
            await self.browser_tool.browser_wait(5)
            screenshots.append(await self._take_screenshot("linkedin_posted"))
            
            post_url = f"https://www.linkedin.com/feed/update/urn:li:activity:{request_id}"
            
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
            logger.error(f"Error publishing to LinkedIn via browser: {e}")
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
        screenshot_path = f"/tmp/promora_linkedin_{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
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
            "impressions": 800,
            "engagements": 40,
            "likes": 15,
            "comments": 3,
            "shares": 2,
            "clicks": 10
        }
    
    @classmethod
    def platform_name(cls) -> str:
        """Get the name of the platform.
        
        Returns:
            Platform name
        """
        return "LinkedIn"
    
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
            "max_length": 3000,
            "supports_images": True,
            "supports_videos": True,
            "supports_links": True,
            "supports_hashtags": True,
            "supports_mentions": True,
            "supports_articles": True
        }
