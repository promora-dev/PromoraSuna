"""
Base adapter for platform publishing.
"""

import abc
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models import PublishRequest, PublishResult, PublishStatus, PlatformAccount


class PlatformAdapter(abc.ABC):
    """Base class for platform-specific publishing adapters."""
    
    def __init__(self, account: PlatformAccount):
        """Initialize the platform adapter.
        
        Args:
            account: Platform account to use for publishing
        """
        self.account = account
    
    @abc.abstractmethod
    async def publish(self, request: PublishRequest) -> PublishResult:
        """Publish content to the platform.
        
        Args:
            request: Publish request with content details
            
        Returns:
            Result of the publishing operation
        """
        pass
    
    @abc.abstractmethod
    async def check_status(self, result_id: str) -> PublishStatus:
        """Check the status of a publishing operation.
        
        Args:
            result_id: ID of the publish result to check
            
        Returns:
            Current status of the publishing operation
        """
        pass
    
    @abc.abstractmethod
    async def get_analytics(self, post_url: str) -> Dict[str, Any]:
        """Get analytics for a published post.
        
        Args:
            post_url: URL of the published post
            
        Returns:
            Analytics data for the post
        """
        pass
    
    @classmethod
    @abc.abstractmethod
    def platform_name(cls) -> str:
        """Get the name of the platform.
        
        Returns:
            Platform name
        """
        pass
    
    @classmethod
    @abc.abstractmethod
    def supports_api(cls) -> bool:
        """Check if the platform supports API publishing.
        
        Returns:
            True if the platform supports API publishing, False otherwise
        """
        pass
    
    @classmethod
    @abc.abstractmethod
    def supports_browser(cls) -> bool:
        """Check if the platform supports browser-based publishing.
        
        Returns:
            True if the platform supports browser-based publishing, False otherwise
        """
        pass
    
    @classmethod
    @abc.abstractmethod
    def content_requirements(cls) -> Dict[str, Any]:
        """Get content requirements for the platform.
        
        Returns:
            Dictionary of content requirements (e.g., max length, supported formats)
        """
        pass
