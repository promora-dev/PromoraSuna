"""
Mock adapter for platform publishing.

This module provides a mock adapter for platform publishing when browser tools are not available.
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from ..models import PublishRequest, PublishResult, PublishStatus, PlatformAccount, PlatformType
from .base import PlatformAdapter
from utils.logger import logger


class MockAdapter(PlatformAdapter):
    """Mock adapter for platform publishing."""
    
    def __init__(self, account: PlatformAccount, browser_tool: Optional[Any] = None):
        """Initialize the mock adapter.
        
        Args:
            account: Platform account to use for publishing
            browser_tool: Browser tool for browser-based publishing (not used)
        """
        super().__init__(account)
        self.platform = account.platform
    
    async def publish(self, request: PublishRequest) -> PublishResult:
        """Publish content to the platform (mock implementation).
        
        Args:
            request: Publish request with content details
            
        Returns:
            Result of the publishing operation
        """
        logger.info(f"[MOCK] Publishing to {self.platform} as {self.account.username}")
        
        result_id = str(uuid.uuid4())
        
        return PublishResult(
            request_id=result_id,
            platform=self.platform,
            account_id=self.account.account_id,
            status=PublishStatus.COMPLETED,
            published_at=datetime.now(),
            post_url=f"https://mock.{self.platform.value.lower()}.com/post/{result_id}",
            content_id=result_id
        )
    
    async def check_status(self, result_id: str) -> PublishStatus:
        """Check the status of a publishing operation (mock implementation).
        
        Args:
            result_id: ID of the publish result to check
            
        Returns:
            Current status of the publishing operation
        """
        logger.info(f"[MOCK] Checking status for {result_id} on {self.platform}")
        return PublishStatus.COMPLETED
    
    async def get_analytics(self, post_url: str) -> Dict[str, Any]:
        """Get analytics for a published post (mock implementation).
        
        Args:
            post_url: URL of the published post
            
        Returns:
            Analytics data for the post
        """
        logger.info(f"[MOCK] Getting analytics for {post_url} on {self.platform}")
        
        return {
            "views": 42,
            "likes": 7,
            "comments": 3,
            "shares": 2
        }
    
    @classmethod
    def platform_name(cls) -> str:
        """Get the name of the platform.
        
        Returns:
            Platform name
        """
        return "Mock Platform"
    
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
        return False
    
    @classmethod
    def content_requirements(cls) -> Dict[str, Any]:
        """Get content requirements for the platform.
        
        Returns:
            Dictionary of content requirements
        """
        return {
            "max_title_length": 100,
            "max_content_length": 1000,
            "supports_images": True,
            "supports_videos": False,
            "supports_links": True
        }
