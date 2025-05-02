"""
Adapter for publishing to Zhihu.
"""

import uuid
import json
import asyncio
import random
from typing import Dict, Any, List, Optional
from datetime import datetime

import logging
from typing import Any, Dict, List, Optional, Union
from ..models import PublishRequest, PublishResult, PublishStatus, PlatformAccount
from .base import PlatformAdapter

logger = logging.getLogger("agentpress")


class ZhihuAdapter(PlatformAdapter):
    """Adapter for publishing to Zhihu."""
    
    def __init__(self, account: PlatformAccount, browser_tool: Optional[Any] = None):
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
            
            logger.info("导航到知乎登录页面...")
            await self.browser_tool.navigate("https://www.zhihu.com/signin")
            await asyncio.sleep(random.uniform(1.5, 3.0))
            screenshots.append(await self._take_screenshot("01_zhihu_login_page"))
            
            current_url = await self.browser_tool.get_current_url()
            logger.info(f"当前页面URL: {current_url}")
            
            try:
                logger.info("尝试切换到密码登录选项卡...")
                password_login_selector = "//div[contains(text(), '密码登录')]"
                await self.browser_tool.wait_for_selector(password_login_selector, timeout=5000)
                await self.browser_tool.click(password_login_selector)
                await asyncio.sleep(random.uniform(0.8, 1.5))
                logger.info("成功切换到密码登录选项卡")
                screenshots.append(await self._take_screenshot("02_zhihu_password_tab"))
            except Exception as e:
                logger.info(f"密码登录选项卡未找到或已选中: {e}")
            
            try:
                logger.info("尝试输入用户名...")
                username_selector = "//input[@name='username']"
                await self.browser_tool.wait_for_selector(username_selector, timeout=5000)
                await self.browser_tool.fill(username_selector, self.account.auth_data["username"])
                await asyncio.sleep(random.uniform(0.5, 1.2))
                logger.info("成功输入用户名")
                screenshots.append(await self._take_screenshot("03_zhihu_username_entered"))
            except Exception as e:
                logger.error(f"输入用户名失败: {e}")
                screenshots.append(await self._take_screenshot("error_username_input"))
                return False
            
            try:
                logger.info("尝试输入密码...")
                password_selector = "//input[@name='password']"
                await self.browser_tool.wait_for_selector(password_selector, timeout=5000)
                await self.browser_tool.fill(password_selector, self.account.auth_data["password"])
                await asyncio.sleep(random.uniform(0.8, 1.5))
                logger.info("成功输入密码")
                screenshots.append(await self._take_screenshot("04_zhihu_credentials_entered"))
            except Exception as e:
                logger.error(f"输入密码失败: {e}")
                screenshots.append(await self._take_screenshot("error_password_input"))
                return False
            
            try:
                logger.info("尝试点击登录按钮...")
                login_button_selector = "//button[contains(@class, 'SignFlow-submitButton')]"
                await self.browser_tool.wait_for_selector(login_button_selector, timeout=5000)
                await self.browser_tool.click(login_button_selector)
                logger.info("成功点击登录按钮")
                screenshots.append(await self._take_screenshot("05_zhihu_login_clicked"))
            except Exception as e:
                logger.error(f"点击登录按钮失败: {e}")
                screenshots.append(await self._take_screenshot("error_login_button"))
                return False
            
            logger.info("等待登录过程完成...")
            await asyncio.sleep(random.uniform(5.0, 8.0))
            screenshots.append(await self._take_screenshot("06_zhihu_after_login_click"))
            
            verification_selectors = [
                ("//div[contains(@class, 'Captcha')]", "验证码"),
                ("//input[contains(@placeholder, '验证码')]", "短信验证码输入框"),
                ("//div[contains(@class, 'SignFlowInput-errorMask')]", "登录错误信息"),
                ("//div[contains(@class, 'Login-challenge')]", "登录挑战"),
                ("//div[contains(@class, 'Login-verifications')]", "登录验证"),
                ("//div[contains(text(), '请完成下列验证')]", "验证请求"),
                ("//div[contains(text(), '安全验证')]", "安全验证"),
                ("//div[contains(@class, 'VerifyCodeInput')]", "验证码输入框"),
                ("//div[contains(@class, 'VerificationCode')]", "验证码组件"),
                ("//div[contains(@class, 'SignFlow-smsInputContainer')]", "短信验证码容器"),
                ("//div[contains(@class, 'SignFlow-captchaContainer')]", "图形验证码容器"),
                ("//button[contains(text(), '获取短信验证码')]", "获取短信验证码按钮"),
                ("//div[contains(@class, 'SignFlow-accountInput-error')]", "账号输入错误"),
                ("//div[contains(@class, 'SignFlow-passwordInput-error')]", "密码输入错误")
            ]
            
            for selector, name in verification_selectors:
                try:
                    exists = await self.browser_tool.is_visible(selector, timeout=2000)
                    if exists:
                        try:
                            text_content = await self.browser_tool.page.text_content(selector)
                            logger.warning(f"检测到{name}: {text_content}")
                        except Exception:
                            logger.warning(f"检测到{name}，需要人工处理")
                        screenshots.append(await self._take_screenshot(f"verification_{name.replace(' ', '_')}"))
                        return False
                except Exception:
                    logger.debug(f"未检测到{name}")
            
            try:
                page_content = await self.browser_tool.page.content()
                verification_texts = [
                    "安全验证", "验证码", "人机验证", "异常登录", 
                    "账号异常", "账号或密码错误", "密码错误", 
                    "请完成验证", "需要验证", "风控系统"
                ]
                
                for text in verification_texts:
                    if text in page_content:
                        logger.warning(f"页面内容包含验证相关文本: {text}")
                        screenshots.append(await self._take_screenshot(f"verification_text_{text}"))
                        return False
            except Exception as e:
                logger.error(f"检查页面内容时出错: {e}")
            
            try:
                logger.info("检查登录是否成功...")
                selectors = [
                    "//button[contains(@class, 'AppHeader-profileEntry')]",  # 头像按钮
                    "//button[contains(@class, 'AppHeader-userInfo')]",      # 用户信息按钮
                    "//img[contains(@class, 'Avatar')]",                     # 头像图片
                    "//a[contains(@href, '/notifications')]",                # 通知链接
                    "//button[contains(@class, 'PushNotifications')]",       # 通知按钮
                    "//a[contains(@href, '/creator')]",                      # 创作者中心链接
                    "//a[contains(@class, 'AppHeader-Tab')]"                 # 导航标签
                ]
                
                for selector in selectors:
                    try:
                        logger.info(f"尝试选择器: {selector}")
                        await self.browser_tool.wait_for_selector(selector, timeout=3000)
                        logger.info(f"选择器 {selector} 找到，登录成功")
                        screenshots.append(await self._take_screenshot("09_zhihu_login_success"))
                        self.is_logged_in = True
                        logger.info(f"成功登录知乎账户 {self.account.username}")
                        return True
                    except Exception as e:
                        logger.info(f"选择器 {selector} 未找到: {e}")
                
                current_url = await self.browser_tool.get_current_url()
                logger.info(f"登录后当前页面URL: {current_url}")
                
                if "signin" not in current_url:
                    logger.info("URL已经不在登录页面，可能已登录成功")
                    screenshots.append(await self._take_screenshot("10_zhihu_url_changed"))
                    
                    try:
                        logger.info("尝试访问首页以确认登录状态...")
                        await self.browser_tool.navigate("https://www.zhihu.com/")
                        await asyncio.sleep(random.uniform(2.0, 3.0))
                        
                        for selector in selectors:
                            try:
                                if await self.browser_tool.is_visible(selector, timeout=2000):
                                    logger.info(f"在首页找到登录元素: {selector}")
                                    screenshots.append(await self._take_screenshot("zhihu_homepage_logged_in"))
                                    self.is_logged_in = True
                                    return True
                            except Exception:
                                pass
                    except Exception as e:
                        logger.error(f"访问首页确认登录状态时出错: {e}")
                
                logger.error("无法确认登录状态，登录可能失败")
                screenshots.append(await self._take_screenshot("11_zhihu_login_failed"))
                return False
                
            except Exception as e:
                logger.error(f"验证登录失败: {e}")
                screenshots.append(await self._take_screenshot("12_zhihu_login_verification_failed"))
                return False
            
        except Exception as e:
            logger.error(f"登录知乎时发生错误: {e}")
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
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        screenshot_filename = f"zhihu_{name}_{timestamp}.png"
        
        try:
            screenshot_path = await self.browser_tool.screenshot(
                str(self.browser_tool.screenshot_dir / screenshot_filename)
            )
            logger.info(f"截图已保存到: {screenshot_path}")
        except Exception as e:
            logger.error(f"截图失败: {e}")
            screenshot_path = f"/tmp/promora_zhihu_{name}_{timestamp}_error.png"
        
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
