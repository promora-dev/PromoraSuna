"""
Human-like registration module for platform accounts.

This module provides functionality for registering accounts on various platforms
with human-like behavior to avoid detection as automated processes.
"""

import asyncio
import random
import time
import os
from typing import Dict, List, Optional, Any, Tuple
import logging

try:
    from agent.tools.sb_browser_tool import SandboxBrowserTool
    has_browser_tool = True
except ImportError:
    has_browser_tool = False
    SandboxBrowserTool = Any  # Type alias for type hints

from utils.logger import logger
from .models import PlatformType, PlatformAccount
from .email_client import EmailClient, EmailClientFactory


class HumanRegistration:
    """Human-like registration for platform accounts."""
    
    def __init__(self, browser_tool: Optional[SandboxBrowserTool] = None, 
               email_address: Optional[str] = None, 
               email_password: Optional[str] = None,
               email_provider: str = "gmail"):
        """Initialize the human registration module.
        
        Args:
            browser_tool: Browser tool for browser-based registration
            email_address: Email address for verification code retrieval
            email_password: Password for the email account
            email_provider: Email provider (gmail, outlook, yahoo, etc.)
        """
        self.browser_tool = browser_tool
        self.min_typing_delay = 0.05  # seconds
        self.max_typing_delay = 0.2  # seconds
        self.min_action_delay = 0.5  # seconds
        self.max_action_delay = 2.0  # seconds
        self.min_page_load_delay = 1.0  # seconds
        self.max_page_load_delay = 3.0  # seconds
        self.screenshot_dir = "/tmp/promora_screenshots"
        
        self.email_address = email_address
        self.email_password = email_password
        self.email_provider = email_provider
        self.email_client = None
        
        if email_address and email_password:
            self.email_client = EmailClientFactory.create_client(
                email_address=email_address,
                password=email_password,
                provider=email_provider
            )
    
    async def _human_delay(self, min_delay: float = None, max_delay: float = None) -> None:
        """Simulate human delay between actions.
        
        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
        """
        min_delay = min_delay or self.min_action_delay
        max_delay = max_delay or self.max_action_delay
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def _human_typing(self, text: str, element_selector: str) -> None:
        """Simulate human typing with variable speed.
        
        Args:
            text: Text to type
            element_selector: Selector for the input element
        """
        if not self.browser_tool:
            logger.warning("Browser tool not available for human typing simulation")
            return
        
        await self.browser_tool.click(element_selector)
        await self._human_delay(0.2, 0.5)
        
        for char in text:
            if random.random() < 0.05:
                await self._human_delay(0.5, 1.0)
            
            await self.browser_tool.type(char)
            
            char_delay = random.uniform(self.min_typing_delay, self.max_typing_delay)
            await asyncio.sleep(char_delay)
    
    async def _human_scroll(self, direction: str = "down", amount: int = None) -> None:
        """Simulate human scrolling behavior.
        
        Args:
            direction: Direction to scroll ("up" or "down")
            amount: Amount to scroll in pixels, or None for random
        """
        if not self.browser_tool:
            logger.warning("Browser tool not available for human scrolling simulation")
            return
        
        if amount is None:
            amount = random.randint(100, 500)
        
        if random.random() < 0.3:
            increments = random.randint(2, 4)
            increment_size = amount // increments
            
            for _ in range(increments):
                await self.browser_tool.scroll(direction, increment_size)
                await self._human_delay(0.1, 0.3)
        else:
            await self.browser_tool.scroll(direction, amount)
    
    async def _human_click(self, selector: str) -> None:
        """Simulate human clicking behavior.
        
        Args:
            selector: Element selector to click
        """
        if not self.browser_tool:
            logger.warning("Browser tool not available for human clicking simulation")
            return
        
        if random.random() < 0.3:
            element_pos = await self.browser_tool.get_element_position(selector)
            if element_pos:
                x, y = element_pos
                
                offset_x = random.randint(-20, 20)
                offset_y = random.randint(-20, 20)
                await self.browser_tool.move_mouse(x + offset_x, y + offset_y)
                await self._human_delay(0.1, 0.3)
        
        await self.browser_tool.click(selector)
    
    async def _handle_captcha(self) -> bool:
        """Handle CAPTCHA challenges during registration.
        
        Returns:
            True if CAPTCHA was successfully handled, False otherwise
        """
        if not self.browser_tool:
            logger.warning("Browser tool not available for CAPTCHA handling")
            return False
        
        screenshot_path = f"{self.screenshot_dir}/captcha_{int(time.time())}.png"
        await self.browser_tool.screenshot(screenshot_path)
        
        captcha_types = [
            {"selector": "iframe[src*='recaptcha']", "type": "recaptcha"},
            {"selector": "iframe[src*='hcaptcha']", "type": "hcaptcha"},
            {"selector": "div.captcha-image", "type": "image_captcha"},
            {"selector": "input[placeholder*='captcha' i]", "type": "text_captcha"}
        ]
        
        for captcha_type in captcha_types:
            has_captcha = await self.browser_tool.element_exists(captcha_type["selector"])
            if has_captcha:
                logger.info(f"Detected {captcha_type['type']} CAPTCHA")
                
                if captcha_type["type"] == "recaptcha":
                    return await self._handle_recaptcha()
                elif captcha_type["type"] == "hcaptcha":
                    return await self._handle_hcaptcha()
                elif captcha_type["type"] == "image_captcha":
                    return await self._handle_image_captcha()
                elif captcha_type["type"] == "text_captcha":
                    return await self._handle_text_captcha()
        
        return True  # No CAPTCHA detected
    
    async def _handle_recaptcha(self) -> bool:
        """Handle reCAPTCHA challenges.
        
        Returns:
            True if reCAPTCHA was successfully handled, False otherwise
        """
        if not self.browser_tool:
            return False
        
        recaptcha_frame = await self.browser_tool.find_element("iframe[src*='recaptcha']")
        if not recaptcha_frame:
            logger.error("Could not find reCAPTCHA iframe")
            return False
        
        await self.browser_tool.switch_to_frame(recaptcha_frame)
        
        checkbox = await self.browser_tool.find_element("div.recaptcha-checkbox-border")
        if not checkbox:
            logger.error("Could not find reCAPTCHA checkbox")
            await self.browser_tool.switch_to_default_content()
            return False
        
        await self._human_click("div.recaptcha-checkbox-border")
        await self._human_delay(1.0, 2.0)
        
        await self.browser_tool.switch_to_default_content()
        challenge_frame = await self.browser_tool.find_element("iframe[title*='challenge']")
        
        if challenge_frame:
            logger.warning("reCAPTCHA challenge detected, this requires human intervention")
            screenshot_path = f"{self.screenshot_dir}/recaptcha_challenge_{int(time.time())}.png"
            await self.browser_tool.screenshot(screenshot_path)
            return False
        
        return True
    
    async def _handle_hcaptcha(self) -> bool:
        """Handle hCaptcha challenges.
        
        Returns:
            True if hCaptcha was successfully handled, False otherwise
        """
        logger.warning("hCaptcha handling not fully implemented, may require human intervention")
        return False
    
    async def _handle_image_captcha(self) -> bool:
        """Handle image-based CAPTCHA challenges.
        
        Returns:
            True if image CAPTCHA was successfully handled, False otherwise
        """
        if not self.browser_tool:
            return False
        
        captcha_image = await self.browser_tool.find_element("div.captcha-image img")
        if not captcha_image:
            logger.error("Could not find CAPTCHA image")
            return False
        
        screenshot_path = f"{self.screenshot_dir}/image_captcha_{int(time.time())}.png"
        await self.browser_tool.screenshot_element(captcha_image, screenshot_path)
        
        logger.warning("Image CAPTCHA handling requires OCR integration, not fully implemented")
        return False
    
    async def _handle_text_captcha(self) -> bool:
        """Handle text-based CAPTCHA challenges.
        
        Returns:
            True if text CAPTCHA was successfully handled, False otherwise
        """
        if not self.browser_tool:
            return False
        
        captcha_input = await self.browser_tool.find_element("input[placeholder*='captcha' i]")
        if not captcha_input:
            logger.error("Could not find CAPTCHA input field")
            return False
        
        screenshot_path = f"{self.screenshot_dir}/text_captcha_{int(time.time())}.png"
        await self.browser_tool.screenshot(screenshot_path)
        
        logger.warning("Text CAPTCHA handling requires OCR integration, not fully implemented")
        return False
        
    async def _get_verification_code(self, platform: str, timeout_minutes: int = 10) -> Optional[str]:
        """Get verification code from email for a specific platform.
        
        Args:
            platform: Platform name (x, zhihu, linkedin, medium)
            timeout_minutes: Maximum time to wait for verification code in minutes
            
        Returns:
            Verification code if found, None otherwise
        """
        if not self.email_client:
            logger.warning("Email client not available for verification code retrieval")
            return None
        
        logger.info(f"Waiting for verification code for {platform}...")
        
        if not self.email_client.connected and not await asyncio.to_thread(self.email_client.connect):
            logger.error("Failed to connect to email server")
            return None
        
        try:
            code = await asyncio.to_thread(
                self.email_client.wait_for_verification_code,
                platform,
                timeout_minutes=timeout_minutes,
                check_interval=10
            )
            
            if code:
                logger.info(f"Found verification code for {platform}: {code}")
                return code
            else:
                logger.warning(f"No verification code found for {platform} after {timeout_minutes} minutes")
                return None
        except Exception as e:
            logger.error(f"Error getting verification code: {str(e)}")
            return None
        finally:
            await asyncio.to_thread(self.email_client.disconnect)
            
    async def _handle_verification_code(self, platform: str, input_selector: str, submit_selector: str = None) -> bool:
        """Handle verification code input during registration.
        
        Args:
            platform: Platform name (x, zhihu, linkedin, medium)
            input_selector: Selector for the verification code input field
            submit_selector: Selector for the submit button (optional)
            
        Returns:
            True if verification code was successfully handled, False otherwise
        """
        if not self.browser_tool:
            logger.error("Browser tool not available for verification code handling")
            return False
        
        if not self.email_client:
            logger.warning("Email client not available for verification code retrieval")
            return False
        
        screenshot_path = f"{self.screenshot_dir}/{platform}_verification_before_{int(time.time())}.png"
        await self.browser_tool.screenshot(screenshot_path)
        
        code = await self._get_verification_code(platform)
        
        if not code:
            logger.warning(f"Failed to get verification code for {platform}")
            return False
        
        await self._human_typing(code, input_selector)
        await self._human_delay()
        
        if submit_selector:
            await self._human_click(submit_selector)
            await self._human_delay(1.0, 2.0)
        
        screenshot_path = f"{self.screenshot_dir}/{platform}_verification_after_{int(time.time())}.png"
        await self.browser_tool.screenshot(screenshot_path)
        
        return True
        
    async def _handle_verification_link(self, platform: str) -> bool:
        """Handle verification link during registration.
        
        Args:
            platform: Platform name (x, zhihu, linkedin, medium)
            
        Returns:
            True if verification link was successfully handled, False otherwise
        """
        if not self.browser_tool:
            logger.error("Browser tool not available for verification link handling")
            return False
        
        if not self.email_client:
            logger.warning("Email client not available for verification link retrieval")
            return False
        
        screenshot_path = f"{self.screenshot_dir}/{platform}_verification_link_before_{int(time.time())}.png"
        await self.browser_tool.screenshot(screenshot_path)
        
        verification_link = await asyncio.to_thread(
            self.email_client.get_verification_link,
            platform,
            timeout_minutes=10,
            check_interval=10
        )
        
        if not verification_link:
            logger.warning(f"Failed to get verification link for {platform}")
            return False
        
        logger.info(f"Found verification link for {platform}: {verification_link}")
        
        await self.browser_tool.navigate(verification_link)
        await self._human_delay(self.min_page_load_delay, self.max_page_load_delay)
        
        screenshot_path = f"{self.screenshot_dir}/{platform}_verification_link_after_{int(time.time())}.png"
        await self.browser_tool.screenshot(screenshot_path)
        
        return True
    
    async def register_x_account(self, username: str, email: str, password: str, display_name: str = None) -> Optional[PlatformAccount]:
        """Register a new X (Twitter) account with human-like behavior.
        
        Args:
            username: Desired username
            email: Email address for registration
            password: Password for the account
            display_name: Display name for the account
            
        Returns:
            Registered platform account, or None if registration failed
        """
        if not self.browser_tool:
            logger.error("Browser tool not available for X account registration")
            return None
        
        try:
            await self.browser_tool.navigate("https://twitter.com/i/flow/signup")
            await self._human_delay(self.min_page_load_delay, self.max_page_load_delay)
            
            screenshot_path = f"{self.screenshot_dir}/x_signup_start_{int(time.time())}.png"
            await self.browser_tool.screenshot(screenshot_path)
            
            create_account_button = await self.browser_tool.find_element("div[role='button']:has-text('Create account')")
            if not create_account_button:
                logger.error("Could not find 'Create account' button")
                return None
            
            await self._human_click("div[role='button']:has-text('Create account')")
            await self._human_delay()
            
            display_name = display_name or f"{username.capitalize()} User"
            await self._human_typing(display_name, "input[name='name']")
            await self._human_delay()
            
            use_email_link = await self.browser_tool.find_element("span:has-text('Use email instead')")
            if use_email_link:
                await self._human_click("span:has-text('Use email instead')")
                await self._human_delay()
            
            await self._human_typing(email, "input[name='email']")
            await self._human_delay()
            
            month = random.randint(1, 12)
            month_selector = "select[aria-labelledby*='Month']"
            await self._human_click(month_selector)
            await self._human_delay(0.2, 0.5)
            await self._human_click(f"{month_selector} option[value='{month}']")
            await self._human_delay()
            
            day = random.randint(1, 28)  # Using 28 to be safe for all months
            day_selector = "select[aria-labelledby*='Day']"
            await self._human_click(day_selector)
            await self._human_delay(0.2, 0.5)
            await self._human_click(f"{day_selector} option[value='{day}']")
            await self._human_delay()
            
            current_year = time.localtime().tm_year
            year = random.randint(current_year - 50, current_year - 25)
            year_selector = "select[aria-labelledby*='Year']"
            await self._human_click(year_selector)
            await self._human_delay(0.2, 0.5)
            await self._human_click(f"{year_selector} option[value='{year}']")
            await self._human_delay()
            
            await self._human_click("div[role='button']:has-text('Next')")
            await self._human_delay(1.0, 2.0)
            
            customize_next_button = await self.browser_tool.find_element("div[role='button']:has-text('Next')")
            if customize_next_button:
                await self._human_click("div[role='button']:has-text('Next')")
                await self._human_delay(1.0, 2.0)
            
            username_input = await self.browser_tool.find_element("input[name='username']")
            if username_input:
                await self._human_typing(username, "input[name='username']")
                await self._human_delay()
                
                await self._human_click("div[role='button']:has-text('Next')")
                await self._human_delay(1.0, 2.0)
            
            password_input = await self.browser_tool.find_element("input[name='password']")
            if password_input:
                await self._human_typing(password, "input[name='password']")
                await self._human_delay()
                
                await self._human_click("div[role='button']:has-text('Next')")
                await self._human_delay(1.0, 2.0)
            
            verification_input = await self.browser_tool.find_element("input[name='verfication_code']")
            if verification_input:
                logger.info("Email verification required, attempting to retrieve code...")
                
                if not self.email_client:
                    logger.warning("Email client not available for verification code retrieval")
                    screenshot_path = f"{self.screenshot_dir}/x_verification_{int(time.time())}.png"
                    await self.browser_tool.screenshot(screenshot_path)
                    return None
                
                verification_result = await self._handle_verification_code(
                    platform="x",
                    input_selector="input[name='verfication_code']",
                    submit_selector="div[role='button']:has-text('Next')"
                )
                
                if not verification_result:
                    logger.info("Attempting to use verification link instead of code for X registration...")
                    verification_link_result = await self._handle_verification_link(platform="x")
                    
                    if not verification_link_result:
                        logger.warning("Failed to handle verification for X registration")
                        screenshot_path = f"{self.screenshot_dir}/x_verification_failed_{int(time.time())}.png"
                        await self.browser_tool.screenshot(screenshot_path)
                        return None
                
                await self._human_delay(2.0, 4.0)
            
            captcha_result = await self._handle_captcha()
            if not captcha_result:
                logger.warning("Failed to handle CAPTCHA during X registration")
                return None
            
            success_indicators = [
                "div:has-text('Your account was created successfully')",
                "span:has-text('Home')",
                "a[aria-label='Profile']"
            ]
            
            for indicator in success_indicators:
                if await self.browser_tool.element_exists(indicator):
                    logger.info(f"Successfully registered X account: {username}")
                    
                    account = PlatformAccount(
                        account_id=username,
                        platform=PlatformType.X,
                        username=username,
                        display_name=display_name,
                        auth_type="credentials",
                        auth_data={
                            "username": username,
                            "password": password,
                            "email": email
                        },
                        last_used=None,
                        usage_count=0,
                        status="active"
                    )
                    
                    return account
            
            logger.warning(f"X account registration may have failed for {username}")
            screenshot_path = f"{self.screenshot_dir}/x_registration_result_{int(time.time())}.png"
            await self.browser_tool.screenshot(screenshot_path)
            return None
            
        except Exception as e:
            logger.error(f"Error during X account registration: {e}")
            screenshot_path = f"{self.screenshot_dir}/x_registration_error_{int(time.time())}.png"
            await self.browser_tool.screenshot(screenshot_path)
            return None
    
    async def register_zhihu_account(self, username: str, email: str, password: str, display_name: str = None) -> Optional[PlatformAccount]:
        """Register a new Zhihu account with human-like behavior.
        
        Args:
            username: Desired username
            email: Email address for registration
            password: Password for the account
            display_name: Display name for the account
            
        Returns:
            Registered platform account, or None if registration failed
        """
        if not self.browser_tool:
            logger.error("Browser tool not available for Zhihu account registration")
            return None
        
        try:
            await self.browser_tool.navigate("https://www.zhihu.com/signup")
            await self._human_delay(self.min_page_load_delay, self.max_page_load_delay)
            
            screenshot_path = f"{self.screenshot_dir}/zhihu_signup_start_{int(time.time())}.png"
            await self.browser_tool.screenshot(screenshot_path)
            
            email_tab = await self.browser_tool.find_element("div.SignFlow-tab:has-text('邮箱注册')")
            if email_tab:
                await self._human_click("div.SignFlow-tab:has-text('邮箱注册')")
                await self._human_delay()
            
            await self._human_typing(email, "input[name='email']")
            await self._human_delay()
            
            await self._human_typing(password, "input[name='password']")
            await self._human_delay()
            
            display_name = display_name or f"{username.capitalize()} User"
            username_input = await self.browser_tool.find_element("input[name='username']")
            if username_input:
                await self._human_typing(display_name, "input[name='username']")
                await self._human_delay()
            
            captcha_result = await self._handle_captcha()
            if not captcha_result:
                logger.warning("Failed to handle CAPTCHA during Zhihu registration")
                return None
            
            register_button = await self.browser_tool.find_element("button.SignFlow-submitButton")
            if register_button:
                await self._human_click("button.SignFlow-submitButton")
                await self._human_delay(2.0, 4.0)
            
            verification_input = await self.browser_tool.find_element("input[placeholder*='验证码']")
            if verification_input:
                logger.info("Email verification required, attempting to retrieve code...")
                
                if not self.email_client:
                    logger.warning("Email client not available for verification code retrieval")
                    screenshot_path = f"{self.screenshot_dir}/zhihu_verification_{int(time.time())}.png"
                    await self.browser_tool.screenshot(screenshot_path)
                    return None
                
                verification_result = await self._handle_verification_code(
                    platform="zhihu",
                    input_selector="input[placeholder*='验证码']",
                    submit_selector="button.SignFlow-submitButton"
                )
                
                if not verification_result:
                    logger.info("Attempting to use verification link instead of code for Zhihu registration...")
                    verification_link_result = await self._handle_verification_link(platform="zhihu")
                    
                    if not verification_link_result:
                        logger.warning("Failed to handle verification for Zhihu registration")
                        screenshot_path = f"{self.screenshot_dir}/zhihu_verification_failed_{int(time.time())}.png"
                        await self.browser_tool.screenshot(screenshot_path)
                        return None
                
                await self._human_delay(2.0, 4.0)
            
            success_indicators = [
                "div.AppHeader-profile",
                "button:has-text('写文章')",
                "a.AppHeader-profileAvatar"
            ]
            
            for indicator in success_indicators:
                if await self.browser_tool.element_exists(indicator):
                    logger.info(f"Successfully registered Zhihu account: {username}")
                    
                    account = PlatformAccount(
                        account_id=username,
                        platform=PlatformType.ZHIHU,
                        username=username,
                        display_name=display_name,
                        auth_type="credentials",
                        auth_data={
                            "username": username,
                            "password": password,
                            "email": email
                        },
                        last_used=None,
                        usage_count=0,
                        status="active"
                    )
                    
                    return account
            
            logger.warning(f"Zhihu account registration may have failed for {username}")
            screenshot_path = f"{self.screenshot_dir}/zhihu_registration_result_{int(time.time())}.png"
            await self.browser_tool.screenshot(screenshot_path)
            return None
            
        except Exception as e:
            logger.error(f"Error during Zhihu account registration: {e}")
            screenshot_path = f"{self.screenshot_dir}/zhihu_registration_error_{int(time.time())}.png"
            await self.browser_tool.screenshot(screenshot_path)
            return None
    
    async def register_medium_account(self, username: str, email: str, password: str, display_name: str = None) -> Optional[PlatformAccount]:
        """Register a new Medium account with human-like behavior.
        
        Args:
            username: Desired username
            email: Email address for registration
            password: Password for the account
            display_name: Display name for the account
            
        Returns:
            Registered platform account, or None if registration failed
        """
        if not self.browser_tool:
            logger.error("Browser tool not available for Medium account registration")
            return None
        
        try:
            await self.browser_tool.navigate("https://medium.com/m/signin")
            await self._human_delay(self.min_page_load_delay, self.max_page_load_delay)
            
            screenshot_path = f"{self.screenshot_dir}/medium_signup_start_{int(time.time())}.png"
            await self.browser_tool.screenshot(screenshot_path)
            
            signup_link = await self.browser_tool.find_element("a:has-text('Sign up')")
            if signup_link:
                await self._human_click("a:has-text('Sign up')")
                await self._human_delay(1.0, 2.0)
            
            email_signup_button = await self.browser_tool.find_element("button:has-text('Sign up with email')")
            if email_signup_button:
                await self._human_click("button:has-text('Sign up with email')")
                await self._human_delay()
            
            await self._human_typing(email, "input[type='email']")
            await self._human_delay()
            
            await self._human_click("button:has-text('Continue')")
            await self._human_delay(1.0, 2.0)
            
            display_name = display_name or f"{username.capitalize()} User"
            name_input = await self.browser_tool.find_element("input[name='name']")
            if name_input:
                await self._human_typing(display_name, "input[name='name']")
                await self._human_delay()
            
            password_input = await self.browser_tool.find_element("input[type='password']")
            if password_input:
                await self._human_typing(password, "input[type='password']")
                await self._human_delay()
            
            await self._human_click("button:has-text('Continue')")
            await self._human_delay(1.0, 2.0)
            
            username_input = await self.browser_tool.find_element("input[name='username']")
            if username_input:
                await self._human_typing(username, "input[name='username']")
                await self._human_delay()
                
                await self._human_click("button:has-text('Continue')")
                await self._human_delay(1.0, 2.0)
            
            verification_message = await self.browser_tool.find_element("div:has-text('Check your inbox')")
            if verification_message:
                logger.info("Email verification required, attempting to retrieve code...")
                
                if not self.email_client:
                    logger.warning("Email client not available for verification code retrieval")
                    screenshot_path = f"{self.screenshot_dir}/medium_verification_{int(time.time())}.png"
                    await self.browser_tool.screenshot(screenshot_path)
                    return None
                
                verification_link = await asyncio.to_thread(
                    self.email_client.get_verification_link,
                    "medium",
                    timeout_minutes=10,
                    check_interval=10
                )
                
                if not verification_link:
                    logger.warning("Failed to get verification link for Medium registration")
                    screenshot_path = f"{self.screenshot_dir}/medium_verification_failed_{int(time.time())}.png"
                    await self.browser_tool.screenshot(screenshot_path)
                    return None
                
                await self.browser_tool.navigate(verification_link)
                await self._human_delay(self.min_page_load_delay, self.max_page_load_delay)
                
                screenshot_path = f"{self.screenshot_dir}/medium_verification_link_{int(time.time())}.png"
                await self.browser_tool.screenshot(screenshot_path)
            
            success_indicators = [
                "a[aria-label='Your profile']",
                "a:has-text('Write')",
                "div.metabar-user"
            ]
            
            for indicator in success_indicators:
                if await self.browser_tool.element_exists(indicator):
                    logger.info(f"Successfully registered Medium account: {username}")
                    
                    account = PlatformAccount(
                        account_id=username,
                        platform=PlatformType.MEDIUM,
                        username=username,
                        display_name=display_name,
                        auth_type="credentials",
                        auth_data={
                            "username": username,
                            "password": password,
                            "email": email
                        },
                        last_used=None,
                        usage_count=0,
                        status="active"
                    )
                    
                    return account
            
            logger.warning(f"Medium account registration may have failed for {username}")
            screenshot_path = f"{self.screenshot_dir}/medium_registration_result_{int(time.time())}.png"
            await self.browser_tool.screenshot(screenshot_path)
            return None
            
        except Exception as e:
            logger.error(f"Error during Medium account registration: {e}")
            screenshot_path = f"{self.screenshot_dir}/medium_registration_error_{int(time.time())}.png"
            await self.browser_tool.screenshot(screenshot_path)
            return None
    
    async def register_linkedin_account(self, username: str, email: str, password: str, display_name: str = None, first_name: str = None, last_name: str = None) -> Optional[PlatformAccount]:
        """Register a new LinkedIn account with human-like behavior.
        
        Args:
            username: Desired username
            email: Email address for registration
            password: Password for the account
            display_name: Display name for the account
            first_name: First name for the account
            last_name: Last name for the account
            
        Returns:
            Registered platform account, or None if registration failed
        """
        if not self.browser_tool:
            logger.error("Browser tool not available for LinkedIn account registration")
            return None
        
        try:
            if not first_name or not last_name:
                if display_name:
                    name_parts = display_name.split()
                    if len(name_parts) >= 2:
                        first_name = first_name or name_parts[0]
                        last_name = last_name or " ".join(name_parts[1:])
                    else:
                        first_name = first_name or display_name
                        last_name = last_name or f"{display_name}son"  # Default last name
                else:
                    first_name = first_name or username.capitalize()
                    last_name = last_name or f"{username.capitalize()}son"  # Default last name
            
            await self.browser_tool.navigate("https://www.linkedin.com/signup")
            await self._human_delay(self.min_page_load_delay, self.max_page_load_delay)
            
            screenshot_path = f"{self.screenshot_dir}/linkedin_signup_start_{int(time.time())}.png"
            await self.browser_tool.screenshot(screenshot_path)
            
            await self._human_typing(email, "input#email-address")
            await self._human_delay()
            
            await self._human_typing(password, "input#password")
            await self._human_delay()
            
            join_button = await self.browser_tool.find_element("button:has-text('Join now')")
            if join_button:
                await self._human_click("button:has-text('Join now')")
            else:
                await self._human_click("button:has-text('Continue')")
            
            await self._human_delay(1.0, 2.0)
            
            first_name_input = await self.browser_tool.find_element("input#first-name")
            if first_name_input:
                await self._human_typing(first_name, "input#first-name")
                await self._human_delay()
            
            last_name_input = await self.browser_tool.find_element("input#last-name")
            if last_name_input:
                await self._human_typing(last_name, "input#last-name")
                await self._human_delay()
            
            await self._human_click("button:has-text('Continue')")
            await self._human_delay(1.0, 2.0)
            
            country_dropdown = await self.browser_tool.find_element("select#country")
            if country_dropdown:
                await self._human_click("select#country")
                await self._human_delay(0.2, 0.5)
                await self._human_click("select#country option[value='us']")
                await self._human_delay()
                
                await self._human_click("button:has-text('Continue')")
                await self._human_delay(1.0, 2.0)
            
            captcha_result = await self._handle_captcha()
            if not captcha_result:
                logger.warning("Failed to handle CAPTCHA during LinkedIn registration")
                return None
            
            verification_message = await self.browser_tool.find_element("div:has-text('Verify your email')")
            if verification_message:
                logger.info("Email verification required, attempting to retrieve code...")
                
                if not self.email_client:
                    logger.warning("Email client not available for verification code retrieval")
                    screenshot_path = f"{self.screenshot_dir}/linkedin_verification_{int(time.time())}.png"
                    await self.browser_tool.screenshot(screenshot_path)
                    return None
                
                verification_result = await self._handle_verification_code(
                    platform="linkedin",
                    input_selector="input[name='verification-code']",
                    submit_selector="button:has-text('Submit')"
                )
                
                if not verification_result:
                    verification_link = await asyncio.to_thread(
                        self.email_client.get_verification_link,
                        "linkedin",
                        timeout_minutes=10,
                        check_interval=10
                    )
                    
                    if verification_link:
                        await self.browser_tool.navigate(verification_link)
                        await self._human_delay(self.min_page_load_delay, self.max_page_load_delay)
                        
                        screenshot_path = f"{self.screenshot_dir}/linkedin_verification_link_{int(time.time())}.png"
                        await self.browser_tool.screenshot(screenshot_path)
                    else:
                        logger.warning("Failed to handle verification for LinkedIn registration")
                        screenshot_path = f"{self.screenshot_dir}/linkedin_verification_failed_{int(time.time())}.png"
                        await self.browser_tool.screenshot(screenshot_path)
                        return None
                
                await self._human_delay(2.0, 4.0)
            
            success_indicators = [
                "div.feed-identity-module",
                "a.app-aware-link:has-text('Profile')",
                "div.identity-headline"
            ]
            
            for indicator in success_indicators:
                if await self.browser_tool.element_exists(indicator):
                    logger.info(f"Successfully registered LinkedIn account: {email}")
                    
                    account = PlatformAccount(
                        account_id=email,
                        platform=PlatformType.LINKEDIN,
                        username=email,
                        display_name=f"{first_name} {last_name}",
                        auth_type="credentials",
                        auth_data={
                            "username": email,
                            "password": password,
                            "email": email
                        },
                        last_used=None,
                        usage_count=0,
                        status="active"
                    )
                    
                    return account
            
            logger.warning(f"LinkedIn account registration may have failed for {email}")
            screenshot_path = f"{self.screenshot_dir}/linkedin_registration_result_{int(time.time())}.png"
            await self.browser_tool.screenshot(screenshot_path)
            return None
            
        except Exception as e:
            logger.error(f"Error during LinkedIn account registration: {e}")
            screenshot_path = f"{self.screenshot_dir}/linkedin_registration_error_{int(time.time())}.png"
            await self.browser_tool.screenshot(screenshot_path)
            return None
