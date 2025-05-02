"""
Platform publisher for Promora.

This module provides a central publisher for distributing content to multiple platforms.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

try:
    from agent.tools.sb_browser_tool import SandboxBrowserTool
    has_browser_tool = True
except ImportError:
    has_browser_tool = False
    SandboxBrowserTool = Any  # Type alias for type hints

from utils.logger import logger
from .models import PublishRequest, PublishResult, PublishStatus, PlatformAccount, PlatformType
from .platform_adapters import (
    PlatformAdapter,
    XAdapter,
    LinkedInAdapter,
    MediumAdapter,
    ZhihuAdapter
)


class PlatformPublisher:
    """Central publisher for distributing content to multiple platforms."""
    
    def __init__(self, browser_tool: Optional[SandboxBrowserTool] = None):
        """Initialize the platform publisher.
        
        Args:
            browser_tool: Browser tool for browser-based publishing
        """
        self.browser_tool = browser_tool
        self.platform_adapters: Dict[PlatformType, Dict[str, PlatformAdapter]] = {
            PlatformType.X: {},
            PlatformType.LINKEDIN: {},
            PlatformType.MEDIUM: {},
            PlatformType.ZHIHU: {}
        }
        self.publish_results: Dict[str, PublishResult] = {}
        self.retry_queue: List[Tuple[str, PublishRequest]] = []
        self.max_retries = 3
        self.retry_delay = 60  # seconds
    
    def register_account(self, account: PlatformAccount) -> None:
        """Register a platform account for publishing.
        
        Args:
            account: Platform account to register
        """
        if self.browser_tool is None and account.platform in [PlatformType.ZHIHU]:
            logger.warning(f"Cannot register {account.platform} account without browser tool. Running in demo mode.")
            # Create a mock adapter that will simulate publishing
            adapter = PlatformAdapter(account, None)
        else:
            if account.platform == PlatformType.X:
                adapter = XAdapter(account, self.browser_tool)
            elif account.platform == PlatformType.LINKEDIN:
                adapter = LinkedInAdapter(account, self.browser_tool)
            elif account.platform == PlatformType.MEDIUM:
                adapter = MediumAdapter(account, self.browser_tool)
            elif account.platform == PlatformType.ZHIHU:
                adapter = ZhihuAdapter(account, self.browser_tool)
            else:
                raise ValueError(f"Unsupported platform: {account.platform}")
        
        self.platform_adapters[account.platform][account.account_id] = adapter
        logger.info(f"Registered {account.platform} account: {account.username}")
    
    def register_accounts(self, accounts: List[PlatformAccount]) -> None:
        """Register multiple platform accounts for publishing.
        
        Args:
            accounts: List of platform accounts to register
        """
        for account in accounts:
            self.register_account(account)
    
    async def publish(self, request: PublishRequest) -> PublishResult:
        """Publish content to a platform.
        
        Args:
            request: Publish request with content details
            
        Returns:
            Result of the publishing operation
        """
        if request.platform not in self.platform_adapters:
            return PublishResult(
                request_id=str(uuid.uuid4()),
                platform=request.platform,
                account_id=request.account_id,
                status=PublishStatus.FAILED,
                error_message=f"Unsupported platform: {request.platform}"
            )
        
        if request.account_id not in self.platform_adapters[request.platform]:
            return PublishResult(
                request_id=str(uuid.uuid4()),
                platform=request.platform,
                account_id=request.account_id,
                status=PublishStatus.FAILED,
                error_message=f"Account not registered: {request.account_id}"
            )
        
        adapter = self.platform_adapters[request.platform][request.account_id]
        result = await adapter.publish(request)
        
        self.publish_results[result.request_id] = result
        
        if result.status == PublishStatus.FAILED:
            self.retry_queue.append((result.request_id, request))
        
        return result
    
    async def publish_to_multiple(self, requests: List[PublishRequest]) -> Dict[str, PublishResult]:
        """Publish content to multiple platforms.
        
        Args:
            requests: List of publish requests
            
        Returns:
            Dictionary mapping request IDs to publish results
        """
        tasks = [self.publish(request) for request in requests]
        results = await asyncio.gather(*tasks)
        
        return {result.request_id: result for result in results}
    
    async def check_status(self, request_id: str) -> PublishStatus:
        """Check the status of a publishing operation.
        
        Args:
            request_id: ID of the publish request to check
            
        Returns:
            Current status of the publishing operation
        """
        if request_id not in self.publish_results:
            return PublishStatus.FAILED
        
        result = self.publish_results[request_id]
        
        if result.status in [PublishStatus.COMPLETED, PublishStatus.FAILED]:
            return result.status
        
        platform = result.platform
        account_id = result.account_id
        
        if platform not in self.platform_adapters or account_id not in self.platform_adapters[platform]:
            return PublishStatus.FAILED
        
        adapter = self.platform_adapters[platform][account_id]
        status = await adapter.check_status(request_id)
        
        result.status = status
        self.publish_results[request_id] = result
        
        return status
    
    async def get_analytics(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a published post.
        
        Args:
            request_id: ID of the publish request
            
        Returns:
            Analytics data for the post, or None if not available
        """
        if request_id not in self.publish_results:
            return None
        
        result = self.publish_results[request_id]
        
        if result.status != PublishStatus.COMPLETED or not result.post_url:
            return None
        
        platform = result.platform
        account_id = result.account_id
        
        if platform not in self.platform_adapters or account_id not in self.platform_adapters[platform]:
            return None
        
        adapter = self.platform_adapters[platform][account_id]
        return await adapter.get_analytics(result.post_url)
    
    async def process_retry_queue(self) -> None:
        """Process the retry queue for failed publishing attempts."""
        if not self.retry_queue:
            return
        
        current_time = datetime.now()
        retry_items = []
        
        for request_id, request in self.retry_queue:
            result = self.publish_results[request_id]
            
            if result.published_at and (current_time - result.published_at) < timedelta(seconds=self.retry_delay):
                retry_items.append((request_id, request))
                continue
            
            retry_count = sum(1 for r in self.publish_results.values() 
                             if r.platform == result.platform and r.account_id == result.account_id 
                             and r.status == PublishStatus.FAILED)
            
            if retry_count >= self.max_retries:
                logger.warning(f"Max retries reached for {result.platform} account {result.account_id}")
                continue
            
            logger.info(f"Retrying publish to {result.platform} for account {result.account_id}")
            result.status = PublishStatus.RETRYING
            self.publish_results[request_id] = result
            
            new_result = await self.publish(request)
            
            if new_result.status == PublishStatus.FAILED:
                retry_items.append((request_id, request))
        
        self.retry_queue = retry_items
    
    def get_platform_requirements(self, platform: PlatformType) -> Dict[str, Any]:
        """Get content requirements for a platform.
        
        Args:
            platform: Platform to get requirements for
            
        Returns:
            Dictionary of content requirements
        """
        if platform == PlatformType.X:
            return XAdapter.content_requirements()
        elif platform == PlatformType.LINKEDIN:
            return LinkedInAdapter.content_requirements()
        elif platform == PlatformType.MEDIUM:
            return MediumAdapter.content_requirements()
        elif platform == PlatformType.ZHIHU:
            return ZhihuAdapter.content_requirements()
        else:
            raise ValueError(f"Unsupported platform: {platform}")
    
    def get_all_platform_requirements(self) -> Dict[PlatformType, Dict[str, Any]]:
        """Get content requirements for all supported platforms.
        
        Returns:
            Dictionary mapping platforms to their content requirements
        """
        return {
            PlatformType.X: XAdapter.content_requirements(),
            PlatformType.LINKEDIN: LinkedInAdapter.content_requirements(),
            PlatformType.MEDIUM: MediumAdapter.content_requirements(),
            PlatformType.ZHIHU: ZhihuAdapter.content_requirements()
        }
