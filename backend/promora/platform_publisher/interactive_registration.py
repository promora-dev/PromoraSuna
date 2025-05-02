"""
交互式LLM引导的账户注册模块

该模块提供了使用LLM分析截图并提供交互式引导的账户注册功能，
帮助用户完成复杂的注册流程，如X、知乎等平台的账户注册。
"""

import os
import json
import asyncio
import random
import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime

try:
    from agent.tools.sb_browser_tool import SandboxBrowserTool
    has_browser_tool = True
except ImportError:
    has_browser_tool = False
    SandboxBrowserTool = Any  # Type alias for type hints

from utils.logger import logger
from .models import PlatformType, PlatformAccount
from .email_client import EmailClient, EmailClientFactory
from .verification_dialog import VerificationDialog
from services.mock_vision_llm import mock_analyze_image_with_gpt4_vision as analyze_image_with_gpt4_vision


class InteractiveRegistration:
    """交互式LLM引导的账户注册"""
    
    def __init__(self, browser_tool: Optional[SandboxBrowserTool] = None, 
               email_address: Optional[str] = None, 
               email_password: Optional[str] = None,
               email_provider: str = "gmail",
               api_key: Optional[str] = None,
               verification_callback = None):
        """初始化交互式注册模块
        
        Args:
            browser_tool: 浏览器工具
            email_address: 用于接收验证码的邮箱地址
            email_password: 邮箱密码
            email_provider: 邮箱提供商（gmail, outlook, yahoo等）
            api_key: OpenAI API密钥
            verification_callback: 验证回调函数
        """
        self.browser_tool = browser_tool
        self.min_typing_delay = 0.05  # 秒
        self.max_typing_delay = 0.2  # 秒
        self.min_action_delay = 0.5  # 秒
        self.max_action_delay = 2.0  # 秒
        self.min_page_load_delay = 1.0  # 秒
        self.max_page_load_delay = 3.0  # 秒
        self.screenshot_dir = "/tmp/promora_interactive_registration"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
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
            
        self.api_key = api_key
        self.debug_dir = self.screenshot_dir
        
        self.verification_callback = verification_callback
        self.verification_dialog = None
        
        self.max_retries = 3  # 最大重试次数
        self.current_step = 0  # 当前步骤
        
    def _match_keywords(self, text: str, keywords: List[str]) -> bool:
        """匹配关键词，支持中英文统一判断
        
        Args:
            text: 要检查的文本
            keywords: 关键词列表
            
        Returns:
            是否匹配任一关键词
        """
        return any(kw.lower() in text.lower() for kw in keywords)
        
    async def _human_delay(self, min_delay: float = None, max_delay: float = None) -> None:
        """模拟人类操作之间的延迟
        
        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
        """
        min_delay = min_delay or self.min_action_delay
        max_delay = max_delay or self.max_action_delay
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def _human_typing(self, text: str, coordinates: Tuple[int, int] = None, selector: str = None) -> None:
        """模拟人类输入，带有变速打字效果
        
        Args:
            text: 要输入的文本
            coordinates: 输入框坐标，如果提供则点击该坐标
            selector: 输入框选择器，如果提供则点击该选择器
        """
        if not self.browser_tool:
            logger.warning("浏览器工具不可用，无法模拟人类输入")
            return
            
        try:
            if coordinates:
                x, y = coordinates
                await self.browser_tool.move_mouse(x, y)
                await self._human_delay(0.1, 0.3)
                await self.browser_tool.page.mouse.click(x, y)
            elif selector:
                await self.browser_tool.click(selector)
            else:
                logger.warning("未提供输入框坐标或选择器，无法点击输入框")
                return
                
            await self._human_delay(0.2, 0.5)
            
            for char in text:
                if random.random() < 0.05:  # 偶尔停顿一下，更像人类
                    await self._human_delay(0.5, 1.0)
                
                await self.browser_tool.type(char)
                
                if ord(char) > 127:
                    await asyncio.sleep(random.uniform(0.2, 0.4))
                else:
                    await asyncio.sleep(random.uniform(self.min_typing_delay, self.max_typing_delay))
                
        except Exception as e:
            logger.error(f"人类输入模拟时出错: {e}")
    
    async def _human_click(self, coordinates: Tuple[int, int] = None, selector: str = None) -> None:
        """模拟人类点击行为
        
        Args:
            coordinates: 点击坐标
            selector: 元素选择器
        """
        if not self.browser_tool:
            logger.warning("浏览器工具不可用，无法模拟人类点击")
            return
            
        try:
            if coordinates:
                x, y = coordinates
                
                offset_x = random.randint(-5, 5)
                offset_y = random.randint(-5, 5)
                
                await self.browser_tool.move_mouse(x + offset_x, y + offset_y)
                await self._human_delay(0.1, 0.3)
                
                await self.browser_tool.page.mouse.click(x, y)
                logger.debug(f"点击坐标: ({x}, {y})")
                
            elif selector:
                if random.random() < 0.3:  # 偶尔先移动鼠标到元素附近，更像人类
                    element_pos = await self.browser_tool.get_element_position(selector)
                    if element_pos:
                        x, y = element_pos
                        
                        offset_x = random.randint(-20, 20)
                        offset_y = random.randint(-20, 20)
                        await self.browser_tool.move_mouse(x + offset_x, y + offset_y)
                        await self._human_delay(0.1, 0.3)
                
                await self.browser_tool.click(selector)
                logger.debug(f"点击选择器: {selector}")
                
            else:
                logger.warning("未提供点击坐标或选择器，无法执行点击操作")
                return
                
        except Exception as e:
            logger.error(f"人类点击模拟时出错: {e}")
    
    async def _take_screenshot(self, name: str = None, platform: str = None) -> str:
        """截取当前页面截图
        
        Args:
            name: 截图名称前缀
            platform: 平台名称
            
        Returns:
            截图路径
        """
        if not self.browser_tool:
            logger.warning("浏览器工具不可用，无法截取截图")
            return None
            
        try:
            timestamp = int(datetime.now().timestamp())
            name = name or f"{self.current_step}"
            platform_prefix = f"{platform}_" if platform else ""
            screenshot_path = f"{self.screenshot_dir}/{platform_prefix}step_{name}_{timestamp}.png"
            
            await self.browser_tool.screenshot(screenshot_path)
            logger.debug(f"截图已保存: {screenshot_path}")
            
            return screenshot_path
        except Exception as e:
            logger.error(f"截取截图时出错: {e}")
            return None
    
    def _build_prompt(self, platform: str, step: int) -> str:
        """构建LLM分析提示词
        
        Args:
            platform: 平台名称
            step: 当前步骤
            
        Returns:
            提示词
        """
        if platform == "x":
            return f"""
分析这个X（Twitter）注册页面的截图，当前步骤: {step}。

请提供以下信息：
1. 页面类型（注册初始页面、个人信息页面、邮箱输入页面等）
2. 当前注册步骤
3. 页面上的主要元素（按钮、输入框、下拉菜单等）及其位置坐标
4. 推荐的下一步操作（点击、输入文本、选择选项等）

以JSON格式返回结果，包含以下字段：
{{
    "page_type": "页面类型描述",
    "registration_step": "当前注册步骤",
    "elements": [...],
    "suggested_actions": [...],
    "next_step": "下一步描述"
}}

注意：
1. 所有坐标必须是实际的数字
2. 只返回JSON格式，不要附带解释
"""
        return f"""
分析这个页面截图，当前步骤: {step}。

请提供以下信息：
1. 页面类型
2. 当前操作步骤
3. 页面上的主要元素及其位置坐标
4. 推荐的下一步操作

以JSON格式返回结果，包含以下字段：
{{
    "page_type": "页面类型描述",
    "current_step": "当前操作步骤",
    "elements": [...],
    "suggested_actions": [...],
    "next_step": "下一步描述"
}}

注意：
1. 所有坐标必须是实际的数字
2. 只返回JSON格式，不要附带解释
"""
    
    async def _analyze_current_page(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析当前页面并获取LLM引导
        
        Args:
            context: 上下文信息
            
        Returns:
            LLM分析结果
        """
        context = context or {}
        context["step"] = self.current_step
        platform = context.get("platform", "unknown")
        
        screenshot_path = await self._take_screenshot(f"analyze_{self.current_step}", platform)
        if not screenshot_path:
            logger.error("无法截取截图，无法分析当前页面")
            return {
                "success": False,
                "error": "无法截取截图"
            }
        
        prompt = self._build_prompt(platform, self.current_step)
        
        try:
            result = await analyze_image_with_gpt4_vision(
                image_path=screenshot_path,
                prompt=prompt,
                api_key=self.api_key
            )
            
            if "output" in result and "text" in result["output"]:
                content = result["output"]["text"]
                
                debug_path = os.path.join(self.debug_dir, f"page_analysis_{platform}_{self.current_step}_{os.path.basename(screenshot_path)}.json")
                with open(debug_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "prompt": prompt,
                        "response": content
                    }, f, ensure_ascii=False, indent=2)
                
                try:
                    import re
                    json_match = re.search(r'({.*})', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        analysis = json.loads(json_str)
                        analysis["success"] = True
                        logger.debug(f"页面分析结果: {json.dumps(analysis, ensure_ascii=False)}")
                        return analysis
                    else:
                        logger.warning(f"无法从响应中提取JSON: {content}")
                        return {
                            "success": False,
                            "error": "无法从响应中提取JSON",
                            "raw_response": content
                        }
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON解析错误: {e}")
                    return {
                        "success": False,
                        "error": f"JSON解析错误: {e}",
                        "raw_response": content
                    }
            else:
                logger.warning("API响应格式不正确")
                return {
                    "success": False,
                    "error": "API响应格式不正确",
                    "raw_response": str(result)
                }
        except Exception as e:
            logger.error(f"分析页面时出错: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_suggested_actions(self, actions: List[Dict[str, Any]]) -> bool:
        """执行LLM建议的操作
        
        Args:
            actions: 操作列表
            
        Returns:
            是否成功执行所有操作
        """
        if not actions:
            logger.warning("没有建议的操作")
            return False
            
        for action in actions:
            action_type = action.get("type", "").lower()
            target = action.get("target", "")
            coordinates = action.get("coordinates")
            value = action.get("value")
            selector = action.get("selector")
            
            logger.debug(f"执行操作: {action_type} - {target}")
            
            try:
                if action_type == "click":
                    await self._human_click(coordinates=coordinates, selector=selector)
                elif action_type == "type":
                    await self._human_typing(text=value, coordinates=coordinates, selector=selector)
                elif action_type == "select":
                    if selector and value:
                        await self.browser_tool.select_option(selector, value)
                    elif coordinates:
                        await self._human_click(coordinates=coordinates)
                    elif selector:
                        await self._human_click(selector=selector)
                    else:
                        logger.warning(f"无法执行选择操作，未提供坐标或选择器: {action}")
                        continue
                elif action_type == "wait":
                    wait_time = action.get("duration", 2)
                    logger.debug(f"等待 {wait_time} 秒")
                    await asyncio.sleep(wait_time)
                elif action_type == "scroll":
                    direction = action.get("direction", "down")
                    amount = action.get("amount", 300)
                    await self.browser_tool.scroll(direction, amount)
                elif action_type == "press_key":
                    key = action.get("key")
                    if key:
                        await self.browser_tool.press(key)
                    else:
                        logger.warning(f"无法执行按键操作，未提供按键: {action}")
                        continue
                else:
                    logger.warning(f"未知操作类型: {action_type}")
                    continue
                    
                await self._human_delay()
                
            except Exception as e:
                logger.error(f"执行操作时出错: {action_type} - {target} - {e}")
                return False
                
        return True
    
    async def _handle_verification(self, platform: str, account_id: str) -> bool:
        """处理验证流程
        
        Args:
            platform: 平台名称
            account_id: 账户ID
            
        Returns:
            是否成功处理验证
        """
        if not self.verification_dialog:
            self.verification_dialog = VerificationDialog(
                platform=platform,
                account_id=account_id,
                verification_dir=self.screenshot_dir,
                notification_callback=self.verification_callback
            )
            
        screenshot_path = await self._take_screenshot(f"{platform}_verification_check")
        
        analysis = await self._analyze_current_page(
            context={
                "platform": platform,
                "step": self.current_step,
                "task": "检查验证码"
            }
        )
        
        if not analysis.get("success", False):
            logger.warning("无法分析验证页面")
            return False
            
        page_type = analysis.get("page_type", "").lower()
        if "验证" in page_type or "verification" in page_type or "captcha" in page_type or "code" in page_type:
            logger.info(f"检测到验证页面: {page_type}")
            
            verification_id = f"{platform}_{account_id}_{int(datetime.now().timestamp())}"
            verification_type = "unknown"
            
            if "email" in page_type or "邮箱" in page_type:
                verification_type = "email"
            elif "captcha" in page_type or "图形" in page_type:
                verification_type = "captcha"
            elif "phone" in page_type or "手机" in page_type:
                verification_type = "phone"
                
            verification_details = {
                "platform": platform,
                "account_id": account_id,
                "page_type": page_type,
                "screenshot": screenshot_path
            }
            
            await self.verification_dialog.request_verification(
                verification_id=verification_id,
                verification_type=verification_type,
                details=verification_details
            )
            
            verification_result = await self.verification_dialog.wait_for_verification_result(
                verification_id=verification_id,
                timeout=300  # 5分钟超时
            )
            
            if not verification_result:
                logger.warning(f"验证超时: {verification_id}")
                return False
                
            verification_code = verification_result.get("code")
            verification_action = verification_result.get("action")
            
            if verification_code and verification_action == "submit":
                input_elements = [e for e in analysis.get("elements", []) if e.get("type", "").lower() in ["input", "输入框"]]
                
                if input_elements:
                    input_element = input_elements[0]
                    coordinates = input_element.get("coordinates")
                    
                    await self._human_typing(verification_code, coordinates=coordinates)
                    
                    submit_elements = [e for e in analysis.get("elements", []) if e.get("type", "").lower() in ["button", "按钮"] and ("submit" in e.get("description", "").lower() or "提交" in e.get("description", "").lower() or "verify" in e.get("description", "").lower() or "验证" in e.get("description", "").lower())]
                    
                    if submit_elements:
                        submit_element = submit_elements[0]
                        submit_coordinates = submit_element.get("coordinates")
                        
                        await self._human_click(coordinates=submit_coordinates)
                        await self._human_delay(1.0, 2.0)
                        
                        return True
                    else:
                        logger.warning("未找到提交按钮")
                        return False
                else:
                    logger.warning("未找到验证码输入框")
                    return False
            else:
                logger.warning(f"验证结果无效: {verification_result}")
                return False
                
        return True  # 没有检测到验证页面，视为成功
    
    async def register_x_account(self, username: str, email: str, password: str, display_name: str = None) -> Optional[PlatformAccount]:
        """使用交互式LLM引导注册X账户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            display_name: 显示名称
            
        Returns:
            注册成功的账户信息，失败则返回None
        """
        if not self.browser_tool:
            logger.error("浏览器工具不可用，无法注册X账户")
            return None
            
        display_name = display_name or f"{username.capitalize()} User"
        
        context = {
            "platform": "x",
            "task": "注册X账户",
            "username": username,
            "email": email,
            "display_name": display_name
        }
        
        try:
            logger.info("导航到X注册页面...")
            await self.browser_tool.navigate("https://twitter.com/i/flow/signup")
            await self._human_delay(self.min_page_load_delay, self.max_page_load_delay)
            
            self.current_step = 1
            max_steps = 15  # 最大步骤数，防止无限循环
            
            while self.current_step <= max_steps:
                logger.info(f"执行注册步骤 {self.current_step}...")
                
                if await self.browser_tool.element_exists("text=Use email instead"):
                    logger.info("检测到 'Use email instead' 按钮，执行点击...")
                    await self._human_click(selector="text=Use email instead")
                    await self._human_delay(0.5, 1.0)
                
                analysis = await self._analyze_current_page(context)
                
                if not analysis.get("success", False):
                    logger.error(f"分析页面失败: {analysis.get('error', '未知错误')}")
                    
                    if self.current_step > 1:  # 不在第一步重试
                        retry_screenshot = await self._take_screenshot(f"retry_{self.current_step}")
                        logger.debug(f"重试截图: {retry_screenshot}")
                        await self._human_delay(2.0, 3.0)
                        continue
                    else:
                        return None
                
                page_type = analysis.get("page_type", "").lower()
                if self._match_keywords(page_type, ["验证", "verification", "captcha", "code"]):
                    logger.info(f"检测到验证页面: {page_type}")
                    verification_success = await self._handle_verification("x", username)
                    
                    if not verification_success:
                        logger.warning("验证处理失败")
                        return None
                        
                    await self._human_delay(2.0, 3.0)
                    continue
                
                if self._match_keywords(page_type, ["完成", "成功", "完成注册", "注册成功", "home", "timeline", "feed"]):
                    logger.info("注册完成!")
                    
                    account = PlatformAccount(
                        platform=PlatformType.X,
                        username=username,
                        display_name=display_name,
                        auth_type="credentials",
                        auth_data={
                            "username": username,
                            "password": password,
                            "email": email
                        },
                        status="active"
                    )
                    
                    return account
                
                suggested_actions = analysis.get("suggested_actions", [])
                
                for action in suggested_actions:
                    if action.get("type") == "type" and not action.get("value"):
                        target = action.get("target", "").lower()
                        
                        if "name" in target or "名称" in target or "display" in target:
                            action["value"] = display_name
                        elif "email" in target or "邮箱" in target:
                            action["value"] = email
                        elif "user" in target or "用户名" in target:
                            action["value"] = username
                        elif "password" in target or "密码" in target:
                            action["value"] = password
                        elif "year" in target or "年" in target:
                            action["value"] = str(random.randint(1970, 2000))  # 随机年份
                        elif "month" in target or "月" in target:
                            action["value"] = str(random.randint(1, 12))  # 随机月份
                        elif "day" in target or "日" in target:
                            action["value"] = str(random.randint(1, 28))  # 随机日期
                
                if not suggested_actions:
                    logger.warning(f"步骤 {self.current_step}: 没有建议的操作")
                    
                    common_selectors = [
                        "span:has-text('Create account')",
                        "span:has-text('创建账号')",
                        "span:has-text('Next')",
                        "span:has-text('下一步')",
                        "div[role='button']",
                        "button"
                    ]
                    
                    for selector in common_selectors:
                        if await self.browser_tool.element_exists(selector, timeout=1000):
                            logger.debug(f"找到常见元素: {selector}")
                            await self._human_click(selector=selector)
                            await self._human_delay()
                            break
                    else:
                        logger.warning("未找到任何可交互元素")
                        
                        if self.current_step % 3 == 0:  # 每3步尝试一次
                            logger.debug("尝试按Tab和Enter键")
                            await self.browser_tool.press("Tab")
                            await self._human_delay(0.5, 1.0)
                            await self.browser_tool.press("Enter")
                            await self._human_delay(1.0, 2.0)
                else:
                    success = await self._execute_suggested_actions(suggested_actions)
                    if not success:
                        logger.warning(f"步骤 {self.current_step}: 执行操作失败")
                        
                        if self.current_step > 1:  # 不在第一步重试
                            retry_screenshot = await self._take_screenshot(f"retry_{self.current_step}")
                            logger.debug(f"重试截图: {retry_screenshot}")
                            await self._human_delay(2.0, 3.0)
                            continue
                        else:
                            return None
                
                await self._human_delay(self.min_page_load_delay, self.max_page_load_delay)
                
                self.current_step += 1
                
            logger.warning(f"达到最大步骤数 {max_steps}，注册未完成")
            return None
            
        except Exception as e:
            logger.error(f"注册X账户时出错: {e}")
            error_screenshot = await self._take_screenshot("error")
            logger.debug(f"错误截图: {error_screenshot}")
            return None
