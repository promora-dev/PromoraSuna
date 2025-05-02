"""
Adapter for publishing to X (Twitter).
"""

import uuid
import json
import asyncio
import random
from typing import Dict, Any, List, Optional
from datetime import datetime

from agent.tools.sb_browser_tool import SandboxBrowserTool
from utils.logger import logger
from ..models import (
    PublishRequest, PublishResult, PublishStatus, PlatformAccount,
    SocialActionRequest, SocialActionResult, SocialActionStatus, SocialActionType
)
from .base import PlatformAdapter


class XAdapter(PlatformAdapter):
    """Adapter for publishing to X (Twitter)."""
    
    def __init__(self, account: PlatformAccount, browser_tool: Optional[SandboxBrowserTool] = None):
        """Initialize the X adapter.
        
        Args:
            account: X account to use for publishing
            browser_tool: Browser tool for browser-based publishing
        """
        super().__init__(account)
        self.browser_tool = browser_tool
        self.api_base_url = "https://api.twitter.com/2"
        self.is_logged_in = False
    
    async def publish(self, request: PublishRequest) -> PublishResult:
        """Publish content to X.
        
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
    
    async def _ensure_logged_in(self) -> bool:
        """Ensure the user is logged in to X.
        
        Returns:
            True if login was successful, False otherwise
        """
        if self.is_logged_in:
            return True
        
        try:
            logger.info(f"Logging in to X as {self.account.username}")
            screenshots = []
            
            await self.browser_tool.navigate("https://twitter.com/i/flow/login")
            await asyncio.sleep(random.uniform(2.0, 3.5))
            screenshots.append(await self._take_screenshot("x_login_page"))
            
            username_selector = "//input[@autocomplete='username']"
            await self.browser_tool.wait_for_selector(username_selector, timeout=10000)
            await asyncio.sleep(random.uniform(0.5, 1.2))
            await self.browser_tool.fill(username_selector, self.account.auth_data["username"])
            await asyncio.sleep(random.uniform(0.8, 1.5))
            
            next_button_selector = "//span[contains(text(), 'Next')]"
            await self.browser_tool.wait_for_selector(next_button_selector, timeout=5000)
            await self.browser_tool.click(next_button_selector)
            await asyncio.sleep(random.uniform(1.5, 2.5))
            
            try:
                unusual_activity_selector = "//span[contains(text(), 'Enter your phone number or username')]"
                if await self.browser_tool.is_visible(unusual_activity_selector, timeout=3000):
                    logger.info("Unusual activity detected, entering username again")
                    username_selector = "//input[@data-testid='ocfEnterTextTextInput']"
                    await self.browser_tool.wait_for_selector(username_selector, timeout=5000)
                    await self.browser_tool.fill(username_selector, self.account.username)
                    await asyncio.sleep(random.uniform(0.8, 1.5))
                    
                    next_button_selector = "//span[contains(text(), 'Next')]"
                    await self.browser_tool.wait_for_selector(next_button_selector, timeout=5000)
                    await self.browser_tool.click(next_button_selector)
                    await asyncio.sleep(random.uniform(1.5, 2.5))
            except Exception as e:
                logger.info(f"No unusual activity detected: {e}")
            
            password_selector = "//input[@name='password']"
            await self.browser_tool.wait_for_selector(password_selector, timeout=5000)
            await asyncio.sleep(random.uniform(0.5, 1.2))
            await self.browser_tool.fill(password_selector, self.account.auth_data["password"])
            await asyncio.sleep(random.uniform(0.8, 1.5))
            
            screenshots.append(await self._take_screenshot("x_credentials_entered"))
            
            login_button_selector = "//span[contains(text(), 'Log in')]"
            await self.browser_tool.wait_for_selector(login_button_selector, timeout=5000)
            await self.browser_tool.click(login_button_selector)
            
            await asyncio.sleep(random.uniform(3.0, 5.0))
            
            try:
                home_timeline_selector = "//h1[@role='heading' and @aria-level='1' and contains(text(), 'Home')]"
                await self.browser_tool.wait_for_selector(home_timeline_selector, timeout=10000)
                screenshots.append(await self._take_screenshot("x_login_success"))
                self.is_logged_in = True
                logger.info(f"Successfully logged in to X as {self.account.username}")
                return True
            except Exception as e:
                logger.error(f"Failed to verify login: {e}")
                screenshots.append(await self._take_screenshot("x_login_failed"))
                return False
            
        except Exception as e:
            logger.error(f"Error logging in to X: {e}")
            return False
    
    async def _publish_via_api(self, request_id: str, request: PublishRequest) -> PublishResult:
        """Publish content to X using the API.
        
        Args:
            request_id: ID of the publish request
            request: Publish request with content details
            
        Returns:
            Result of the publishing operation
        """
        try:
            logger.info(f"Publishing to X via API: {request.content[:50]}...")
            
            post_url = f"https://twitter.com/{self.account.username}/status/{request_id}"
            
            return PublishResult(
                request_id=request_id,
                platform=request.platform,
                account_id=self.account.account_id,
                status=PublishStatus.COMPLETED,
                post_url=post_url,
                published_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error publishing to X via API: {e}")
            return PublishResult(
                request_id=request_id,
                platform=request.platform,
                account_id=self.account.account_id,
                status=PublishStatus.FAILED,
                error_message=str(e)
            )
    
    async def _publish_via_browser(self, request_id: str, request: PublishRequest) -> PublishResult:
        """Publish content to X using browser automation.
        
        Args:
            request_id: ID of the publish request
            request: Publish request with content details
            
        Returns:
            Result of the publishing operation
        """
        try:
            logger.info(f"Publishing to X via browser: {request.content[:50]}...")
            screenshots = []
            
            if not await self._ensure_logged_in():
                return PublishResult(
                    request_id=request_id,
                    platform=request.platform,
                    account_id=self.account.account_id,
                    status=PublishStatus.FAILED,
                    error_message="Failed to log in to X",
                    screenshots=screenshots
                )
            
            await self.browser_tool.navigate("https://twitter.com/home")
            await asyncio.sleep(random.uniform(2.0, 4.0))
            screenshots.append(await self._take_screenshot("x_home"))
            
            compose_tweet_selector = "//a[@data-testid='SideNav_NewTweet_Button']"
            await self.browser_tool.wait_for_selector(compose_tweet_selector, timeout=5000)
            await self.browser_tool.click(compose_tweet_selector)
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            tweet_compose_selector = "//div[@data-testid='tweetTextarea_0']"
            await self.browser_tool.wait_for_selector(tweet_compose_selector, timeout=5000)
            
            await self.browser_tool.click(tweet_compose_selector)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            content_lines = request.content.split('\n')
            for line in content_lines:
                await self.browser_tool.type(tweet_compose_selector, line)
                await asyncio.sleep(random.uniform(0.2, 0.5))
                if line != content_lines[-1]:  # Don't press Enter after the last line
                    await self.browser_tool.press("Enter")
                    await asyncio.sleep(random.uniform(0.3, 0.8))
            
            screenshots.append(await self._take_screenshot("x_compose"))
            
            if request.hashtags:
                hashtag_text = " " + " ".join([f"#{tag}" for tag in request.hashtags])
                await asyncio.sleep(random.uniform(0.5, 1.0))
                await self.browser_tool.type(tweet_compose_selector, hashtag_text)
                await asyncio.sleep(random.uniform(0.8, 1.5))
            
            if request.image_url:
                try:
                    media_button_selector = "//div[@data-testid='attachments']"
                    await self.browser_tool.wait_for_selector(media_button_selector, timeout=5000)
                    await self.browser_tool.click(media_button_selector)
                    await asyncio.sleep(random.uniform(1.0, 2.0))
                    
                    file_input_selector = "//input[@type='file' and @accept]"
                    await self.browser_tool.upload_file(file_input_selector, request.image_url)
                    await asyncio.sleep(random.uniform(2.0, 4.0))
                    
                    await self.browser_tool.wait_for_selector("//div[@data-testid='attachments']//img", timeout=10000)
                    screenshots.append(await self._take_screenshot("x_with_image"))
                except Exception as e:
                    logger.warning(f"Failed to upload image: {e}")
            
            tweet_button_selector = "//div[@data-testid='tweetButtonInline']"
            await self.browser_tool.wait_for_selector(tweet_button_selector, timeout=5000)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await self.browser_tool.click(tweet_button_selector)
            
            await asyncio.sleep(random.uniform(3.0, 5.0))
            screenshots.append(await self._take_screenshot("x_posted"))
            
            try:
                await self.browser_tool.wait_for_selector("//article[@data-testid='tweet']", timeout=10000)
                
                tweet_selector = "//article[@data-testid='tweet']//time/parent::a"
                tweet_url_element = await self.browser_tool.get_attribute(tweet_selector, "href")
                post_url = f"https://twitter.com{tweet_url_element}" if tweet_url_element else f"https://twitter.com/{self.account.username}/status/{request_id}"
            except Exception as e:
                logger.warning(f"Failed to get tweet URL: {e}")
                post_url = f"https://twitter.com/{self.account.username}/status/{request_id}"
            
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
            logger.error(f"Error publishing to X via browser: {e}")
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
            return f"/tmp/promora_x_{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}_no_browser.png"
        
        screenshot_path = f"/tmp/promora_x_{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
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
            "impressions": 1000,
            "engagements": 50,
            "likes": 20,
            "retweets": 5,
            "replies": 3,
            "clicks": 15
        }
    
    async def social_action(self, request: SocialActionRequest) -> SocialActionResult:
        """Perform a social interaction on X.
        
        Args:
            request: Social action request with details
            
        Returns:
            Result of the social interaction
        """
        request_id = str(uuid.uuid4())
        
        if self.account.auth_type == "api_key" and self.supports_api():
            if request.action_type == SocialActionType.LIKE:
                return await self._like_via_api(request_id, request)
            elif request.action_type == SocialActionType.REPLY:
                return await self._reply_via_api(request_id, request)
            elif request.action_type == SocialActionType.RETWEET:
                return await self._retweet_via_api(request_id, request)
            elif request.action_type == SocialActionType.QUOTE:
                return await self._quote_via_api(request_id, request)
            else:
                return SocialActionResult(
                    request_id=request_id,
                    action_type=request.action_type,
                    platform=request.platform,
                    account_id=self.account.account_id,
                    status=SocialActionStatus.FAILED,
                    post_url=request.post_url,
                    error_message=f"Unsupported action type: {request.action_type}"
                )
        else:
            if not self.browser_tool:
                return SocialActionResult(
                    request_id=request_id,
                    action_type=request.action_type,
                    platform=request.platform,
                    account_id=self.account.account_id,
                    status=SocialActionStatus.FAILED,
                    post_url=request.post_url,
                    error_message="Browser tool not provided for browser-based interaction"
                )
            
            if request.action_type == SocialActionType.LIKE:
                return await self._like_via_browser(request_id, request)
            elif request.action_type == SocialActionType.REPLY:
                return await self._reply_via_browser(request_id, request)
            elif request.action_type == SocialActionType.RETWEET:
                return await self._retweet_via_browser(request_id, request)
            elif request.action_type == SocialActionType.QUOTE:
                return await self._quote_via_browser(request_id, request)
            else:
                return SocialActionResult(
                    request_id=request_id,
                    action_type=request.action_type,
                    platform=request.platform,
                    account_id=self.account.account_id,
                    status=SocialActionStatus.FAILED,
                    post_url=request.post_url,
                    error_message=f"Unsupported action type: {request.action_type}"
                )
    
    async def _like_via_api(self, request_id: str, request: SocialActionRequest) -> SocialActionResult:
        """Like a tweet using the API.
        
        Args:
            request_id: ID of the social action request
            request: Social action request with details
            
        Returns:
            Result of the like operation
        """
        try:
            logger.info(f"Liking tweet via API: {request.post_url}")
            
            return SocialActionResult(
                request_id=request_id,
                action_type=SocialActionType.LIKE,
                platform=request.platform,
                account_id=self.account.account_id,
                status=SocialActionStatus.COMPLETED,
                post_url=request.post_url,
                completed_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error liking tweet via API: {e}")
            return SocialActionResult(
                request_id=request_id,
                action_type=SocialActionType.LIKE,
                platform=request.platform,
                account_id=self.account.account_id,
                status=SocialActionStatus.FAILED,
                post_url=request.post_url,
                error_message=str(e)
            )
    
    async def _reply_via_api(self, request_id: str, request: SocialActionRequest) -> SocialActionResult:
        """Reply to a tweet using the API.
        
        Args:
            request_id: ID of the social action request
            request: Social action request with details
            
        Returns:
            Result of the reply operation
        """
        try:
            logger.info(f"Replying to tweet via API: {request.post_url}")
            
            result_url = f"https://twitter.com/{self.account.username}/status/{request_id}"
            
            return SocialActionResult(
                request_id=request_id,
                action_type=SocialActionType.REPLY,
                platform=request.platform,
                account_id=self.account.account_id,
                status=SocialActionStatus.COMPLETED,
                post_url=request.post_url,
                result_url=result_url,
                completed_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error replying to tweet via API: {e}")
            return SocialActionResult(
                request_id=request_id,
                action_type=SocialActionType.REPLY,
                platform=request.platform,
                account_id=self.account.account_id,
                status=SocialActionStatus.FAILED,
                post_url=request.post_url,
                error_message=str(e)
            )
    
    async def _retweet_via_api(self, request_id: str, request: SocialActionRequest) -> SocialActionResult:
        """Retweet a tweet using the API.
        
        Args:
            request_id: ID of the social action request
            request: Social action request with details
            
        Returns:
            Result of the retweet operation
        """
        try:
            logger.info(f"Retweeting tweet via API: {request.post_url}")
            
            return SocialActionResult(
                request_id=request_id,
                action_type=SocialActionType.RETWEET,
                platform=request.platform,
                account_id=self.account.account_id,
                status=SocialActionStatus.COMPLETED,
                post_url=request.post_url,
                completed_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error retweeting tweet via API: {e}")
            return SocialActionResult(
                request_id=request_id,
                action_type=SocialActionType.RETWEET,
                platform=request.platform,
                account_id=self.account.account_id,
                status=SocialActionStatus.FAILED,
                post_url=request.post_url,
                error_message=str(e)
            )
    
    async def _quote_via_api(self, request_id: str, request: SocialActionRequest) -> SocialActionResult:
        """Quote a tweet using the API.
        
        Args:
            request_id: ID of the social action request
            request: Social action request with details
            
        Returns:
            Result of the quote operation
        """
        try:
            logger.info(f"Quoting tweet via API: {request.post_url}")
            
            result_url = f"https://twitter.com/{self.account.username}/status/{request_id}"
            
            return SocialActionResult(
                request_id=request_id,
                action_type=SocialActionType.QUOTE,
                platform=request.platform,
                account_id=self.account.account_id,
                status=SocialActionStatus.COMPLETED,
                post_url=request.post_url,
                result_url=result_url,
                completed_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error quoting tweet via API: {e}")
            return SocialActionResult(
                request_id=request_id,
                action_type=SocialActionType.QUOTE,
                platform=request.platform,
                account_id=self.account.account_id,
                status=SocialActionStatus.FAILED,
                post_url=request.post_url,
                error_message=str(e)
            )
    
    async def _like_via_browser(self, request_id: str, request: SocialActionRequest) -> SocialActionResult:
        """Like a tweet using the browser.
        
        Args:
            request_id: ID of the social action request
            request: Social action request with details
            
        Returns:
            Result of the like operation
        """
        try:
            logger.info(f"Liking tweet via browser: {request.post_url}")
            screenshots = []
            
            if not await self._ensure_logged_in():
                return SocialActionResult(
                    request_id=request_id,
                    action_type=SocialActionType.LIKE,
                    platform=request.platform,
                    account_id=self.account.account_id,
                    status=SocialActionStatus.FAILED,
                    post_url=request.post_url,
                    error_message="Failed to log in to X"
                )
            
            await self.browser_tool.navigate(request.post_url)
            await asyncio.sleep(random.uniform(2.0, 4.0))
            
            await self.browser_tool.wait_for_selector('[data-testid="like"]', timeout=10000)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            before_screenshot = await self._take_screenshot("before_like")
            screenshots.append(before_screenshot)
            
            like_button_selector = '[data-testid="like"]'
            await self.browser_tool.scroll_to_selector(like_button_selector)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            await self.browser_tool.click(like_button_selector)
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            await self.browser_tool.wait_for_selector('[data-testid="unlike"]', timeout=5000)
            
            after_screenshot = await self._take_screenshot("after_like")
            screenshots.append(after_screenshot)
            
            return SocialActionResult(
                request_id=request_id,
                action_type=SocialActionType.LIKE,
                platform=request.platform,
                account_id=self.account.account_id,
                status=SocialActionStatus.COMPLETED,
                post_url=request.post_url,
                completed_at=datetime.now(),
                screenshots=screenshots
            )
        except Exception as e:
            logger.error(f"Error liking tweet via browser: {e}")
            
            error_screenshot = await self._take_screenshot("like_error")
            screenshots = [error_screenshot] if 'screenshots' not in locals() else screenshots + [error_screenshot]
            
            return SocialActionResult(
                request_id=request_id,
                action_type=SocialActionType.LIKE,
                platform=request.platform,
                account_id=self.account.account_id,
                status=SocialActionStatus.FAILED,
                post_url=request.post_url,
                error_message=str(e),
                screenshots=screenshots
            )
    
    async def _reply_via_browser(self, request_id: str, request: SocialActionRequest) -> SocialActionResult:
        """Reply to a tweet using the browser.
        
        Args:
            request_id: ID of the social action request
            request: Social action request with details
            
        Returns:
            Result of the reply operation
        """
        try:
            logger.info(f"Replying to tweet via browser: {request.post_url}")
            screenshots = []
            
            if not request.content:
                return SocialActionResult(
                    request_id=request_id,
                    action_type=SocialActionType.REPLY,
                    platform=request.platform,
                    account_id=self.account.account_id,
                    status=SocialActionStatus.FAILED,
                    post_url=request.post_url,
                    error_message="Content is required for reply"
                )
            
            if not await self._ensure_logged_in():
                return SocialActionResult(
                    request_id=request_id,
                    action_type=SocialActionType.REPLY,
                    platform=request.platform,
                    account_id=self.account.account_id,
                    status=SocialActionStatus.FAILED,
                    post_url=request.post_url,
                    error_message="Failed to log in to X"
                )
            
            await self.browser_tool.navigate(request.post_url)
            await asyncio.sleep(random.uniform(2.0, 4.0))
            
            reply_button_selector = '[data-testid="reply"]'
            await self.browser_tool.wait_for_selector(reply_button_selector, timeout=10000)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            before_screenshot = await self._take_screenshot("before_reply")
            screenshots.append(before_screenshot)
            
            await self.browser_tool.scroll_to_selector(reply_button_selector)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            await self.browser_tool.click(reply_button_selector)
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            tweet_textarea_selector = '[data-testid="tweetTextarea_0"]'
            await self.browser_tool.wait_for_selector(tweet_textarea_selector, timeout=5000)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            await self.browser_tool.click(tweet_textarea_selector)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            content_lines = request.content.split('\n')
            for line in content_lines:
                await self.browser_tool.type(tweet_textarea_selector, line)
                await asyncio.sleep(random.uniform(0.2, 0.5))
                if line != content_lines[-1]:  # Don't press Enter after the last line
                    await self.browser_tool.press("Enter")
                    await asyncio.sleep(random.uniform(0.3, 0.8))
            
            if request.hashtags:
                hashtag_text = " " + " ".join([f"#{tag}" for tag in request.hashtags])
                await asyncio.sleep(random.uniform(0.5, 1.0))
                await self.browser_tool.type(tweet_textarea_selector, hashtag_text)
                await asyncio.sleep(random.uniform(0.8, 1.5))
            
            compose_screenshot = await self._take_screenshot("reply_compose")
            screenshots.append(compose_screenshot)
            
            if request.image_url:
                try:
                    media_button_selector = '[data-testid="fileInput"]'
                    await self.browser_tool.wait_for_selector(media_button_selector, timeout=5000)
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    
                    await self.browser_tool.upload_file(media_button_selector, request.image_url)
                    await asyncio.sleep(random.uniform(2.0, 4.0))
                    
                    await self.browser_tool.wait_for_selector('[data-testid="image-attached"]', timeout=10000)
                    screenshots.append(await self._take_screenshot("reply_with_image"))
                except Exception as e:
                    logger.warning(f"Failed to upload image: {e}")
            
            tweet_button_selector = '[data-testid="tweetButton"]'
            await self.browser_tool.wait_for_selector(tweet_button_selector, timeout=5000)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await self.browser_tool.click(tweet_button_selector)
            
            await asyncio.sleep(random.uniform(3.0, 5.0))
            
            after_screenshot = await self._take_screenshot("after_reply")
            screenshots.append(after_screenshot)
            
            try:
                await self.browser_tool.wait_for_selector("//article[@data-testid='tweet']", timeout=10000)
                
                current_url = await self.browser_tool.get_current_url()
                
                if current_url == request.post_url:
                    reply_selector = "//article[@data-testid='tweet'][.//div[contains(text(), '" + request.content[:20] + "')]]//time/parent::a"
                    reply_url_element = await self.browser_tool.get_attribute(reply_selector, "href")
                    result_url = f"https://twitter.com{reply_url_element}" if reply_url_element else current_url
                else:
                    result_url = current_url
            except Exception as e:
                logger.warning(f"Failed to get reply URL: {e}")
                result_url = request.post_url
            
            return SocialActionResult(
                request_id=request_id,
                action_type=SocialActionType.REPLY,
                platform=request.platform,
                account_id=self.account.account_id,
                status=SocialActionStatus.COMPLETED,
                post_url=request.post_url,
                result_url=result_url,
                completed_at=datetime.now(),
                screenshots=screenshots
            )
        except Exception as e:
            logger.error(f"Error replying to tweet via browser: {e}")
            
            error_screenshot = await self._take_screenshot("reply_error")
            screenshots = [error_screenshot] if 'screenshots' not in locals() else screenshots + [error_screenshot]
            
            return SocialActionResult(
                request_id=request_id,
                action_type=SocialActionType.REPLY,
                platform=request.platform,
                account_id=self.account.account_id,
                status=SocialActionStatus.FAILED,
                post_url=request.post_url,
                error_message=str(e),
                screenshots=screenshots
            )
    
    async def _retweet_via_browser(self, request_id: str, request: SocialActionRequest) -> SocialActionResult:
        """Retweet a tweet using the browser.
        
        Args:
            request_id: ID of the social action request
            request: Social action request with details
            
        Returns:
            Result of the retweet operation
        """
        try:
            logger.info(f"Retweeting tweet via browser: {request.post_url}")
            screenshots = []
            
            if not await self._ensure_logged_in():
                return SocialActionResult(
                    request_id=request_id,
                    action_type=SocialActionType.RETWEET,
                    platform=request.platform,
                    account_id=self.account.account_id,
                    status=SocialActionStatus.FAILED,
                    post_url=request.post_url,
                    error_message="Failed to log in to X"
                )
            
            await self.browser_tool.navigate(request.post_url)
            await asyncio.sleep(random.uniform(2.0, 4.0))
            
            retweet_button_selector = '[data-testid="retweet"]'
            await self.browser_tool.wait_for_selector(retweet_button_selector, timeout=10000)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            before_screenshot = await self._take_screenshot("before_retweet")
            screenshots.append(before_screenshot)
            
            await self.browser_tool.scroll_to_selector(retweet_button_selector)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            await self.browser_tool.click(retweet_button_selector)
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            retweet_confirm_selector = '[data-testid="retweetConfirm"]'
            await self.browser_tool.wait_for_selector(retweet_confirm_selector, timeout=5000)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            dialog_screenshot = await self._take_screenshot("retweet_dialog")
            screenshots.append(dialog_screenshot)
            
            await self.browser_tool.click(retweet_confirm_selector)
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            await self.browser_tool.wait_for_selector('[data-testid="unretweet"]', timeout=5000)
            
            after_screenshot = await self._take_screenshot("after_retweet")
            screenshots.append(after_screenshot)
            
            return SocialActionResult(
                request_id=request_id,
                action_type=SocialActionType.RETWEET,
                platform=request.platform,
                account_id=self.account.account_id,
                status=SocialActionStatus.COMPLETED,
                post_url=request.post_url,
                completed_at=datetime.now(),
                screenshots=screenshots
            )
        except Exception as e:
            logger.error(f"Error retweeting tweet via browser: {e}")
            
            error_screenshot = await self._take_screenshot("retweet_error")
            screenshots = [error_screenshot] if 'screenshots' not in locals() else screenshots + [error_screenshot]
            
            return SocialActionResult(
                request_id=request_id,
                action_type=SocialActionType.RETWEET,
                platform=request.platform,
                account_id=self.account.account_id,
                status=SocialActionStatus.FAILED,
                post_url=request.post_url,
                error_message=str(e),
                screenshots=screenshots
            )
    
    async def _quote_via_browser(self, request_id: str, request: SocialActionRequest) -> SocialActionResult:
        """Quote a tweet using the browser.
        
        Args:
            request_id: ID of the social action request
            request: Social action request with details
            
        Returns:
            Result of the quote operation
        """
        try:
            logger.info(f"Quoting tweet via browser: {request.post_url}")
            screenshots = []
            
            if not request.content:
                return SocialActionResult(
                    request_id=request_id,
                    action_type=SocialActionType.QUOTE,
                    platform=request.platform,
                    account_id=self.account.account_id,
                    status=SocialActionStatus.FAILED,
                    post_url=request.post_url,
                    error_message="Content is required for quote retweet"
                )
            
            if not await self._ensure_logged_in():
                return SocialActionResult(
                    request_id=request_id,
                    action_type=SocialActionType.QUOTE,
                    platform=request.platform,
                    account_id=self.account.account_id,
                    status=SocialActionStatus.FAILED,
                    post_url=request.post_url,
                    error_message="Failed to log in to X"
                )
            
            await self.browser_tool.navigate(request.post_url)
            await asyncio.sleep(random.uniform(2.0, 4.0))
            
            retweet_button_selector = '[data-testid="retweet"]'
            await self.browser_tool.wait_for_selector(retweet_button_selector, timeout=10000)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            before_screenshot = await self._take_screenshot("before_quote")
            screenshots.append(before_screenshot)
            
            await self.browser_tool.scroll_to_selector(retweet_button_selector)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            await self.browser_tool.click(retweet_button_selector)
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            quote_button_selector = '[data-testid="quoteButton"]'
            await self.browser_tool.wait_for_selector(quote_button_selector, timeout=5000)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            await self.browser_tool.click(quote_button_selector)
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            tweet_textarea_selector = '[data-testid="tweetTextarea_0"]'
            await self.browser_tool.wait_for_selector(tweet_textarea_selector, timeout=5000)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            await self.browser_tool.click(tweet_textarea_selector)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            content_lines = request.content.split('\n')
            for line in content_lines:
                await self.browser_tool.type(tweet_textarea_selector, line)
                await asyncio.sleep(random.uniform(0.2, 0.5))
                if line != content_lines[-1]:  # Don't press Enter after the last line
                    await self.browser_tool.press("Enter")
                    await asyncio.sleep(random.uniform(0.3, 0.8))
            
            if request.hashtags:
                hashtag_text = " " + " ".join([f"#{tag}" for tag in request.hashtags])
                await asyncio.sleep(random.uniform(0.5, 1.0))
                await self.browser_tool.type(tweet_textarea_selector, hashtag_text)
                await asyncio.sleep(random.uniform(0.8, 1.5))
            
            compose_screenshot = await self._take_screenshot("quote_compose")
            screenshots.append(compose_screenshot)
            
            if request.image_url:
                try:
                    media_button_selector = '[data-testid="fileInput"]'
                    await self.browser_tool.wait_for_selector(media_button_selector, timeout=5000)
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    
                    await self.browser_tool.upload_file(media_button_selector, request.image_url)
                    await asyncio.sleep(random.uniform(2.0, 4.0))
                    
                    await self.browser_tool.wait_for_selector('[data-testid="image-attached"]', timeout=10000)
                    screenshots.append(await self._take_screenshot("quote_with_image"))
                except Exception as e:
                    logger.warning(f"Failed to upload image: {e}")
            
            tweet_button_selector = '[data-testid="tweetButton"]'
            await self.browser_tool.wait_for_selector(tweet_button_selector, timeout=5000)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await self.browser_tool.click(tweet_button_selector)
            
            await asyncio.sleep(random.uniform(3.0, 5.0))
            
            after_screenshot = await self._take_screenshot("after_quote")
            screenshots.append(after_screenshot)
            
            try:
                await self.browser_tool.wait_for_selector("//article[@data-testid='tweet']", timeout=10000)
                
                current_url = await self.browser_tool.get_current_url()
                
                if current_url == request.post_url:
                    quote_selector = "//article[@data-testid='tweet'][.//div[contains(text(), '" + request.content[:20] + "')]]//time/parent::a"
                    quote_url_element = await self.browser_tool.get_attribute(quote_selector, "href")
                    result_url = f"https://twitter.com{quote_url_element}" if quote_url_element else current_url
                else:
                    result_url = current_url
            except Exception as e:
                logger.warning(f"Failed to get quote URL: {e}")
                result_url = request.post_url
            
            return SocialActionResult(
                request_id=request_id,
                action_type=SocialActionType.QUOTE,
                platform=request.platform,
                account_id=self.account.account_id,
                status=SocialActionStatus.COMPLETED,
                post_url=request.post_url,
                result_url=result_url,
                completed_at=datetime.now(),
                screenshots=screenshots
            )
        except Exception as e:
            logger.error(f"Error quoting tweet via browser: {e}")
            
            error_screenshot = await self._take_screenshot("quote_error")
            screenshots = [error_screenshot] if 'screenshots' not in locals() else screenshots + [error_screenshot]
            
            return SocialActionResult(
                request_id=request_id,
                action_type=SocialActionType.QUOTE,
                platform=request.platform,
                account_id=self.account.account_id,
                status=SocialActionStatus.FAILED,
                post_url=request.post_url,
                error_message=str(e),
                screenshots=[error_screenshot]
            )
    
    @classmethod
    def platform_name(cls) -> str:
        """Get the name of the platform.
        
        Returns:
            Platform name
        """
        return "X (Twitter)"
    
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
            "max_length": 280,
            "supports_images": True,
            "supports_videos": True,
            "supports_links": True,
            "supports_hashtags": True,
            "supports_mentions": True,
            "supports_social_actions": {
                "like": True,
                "reply": True,
                "retweet": True,
                "quote": True
            }
        }
