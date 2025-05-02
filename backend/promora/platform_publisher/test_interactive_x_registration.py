"""
交互式LLM引导的X账户注册测试脚本

此脚本演示如何使用交互式LLM引导系统进行X平台账户注册，
通过LLM分析截图并提供操作建议，实现更智能的注册流程。
"""

import os
import json
import time
import asyncio
import random
import logging
import sys
import string
import traceback
import argparse
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

try:
    from agent.tools.sb_browser_tool import SandboxBrowserTool
    has_browser_tool = True
except ImportError:
    has_browser_tool = False
    SandboxBrowserTool = Any

from .test_browser_tool import TestBrowserTool
from .verification_dialog import VerificationDialog
from .models import PlatformAccount, PlatformType
from .email_client import EmailClientFactory
from services.mock_vision_llm import mock_analyze_image_with_gpt4_vision as analyze_image_with_gpt4_vision

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/tmp/promora_interactive_x_registration_debug.log")
    ]
)
logger = logging.getLogger("interactive_x_registration")

logging.getLogger("playwright").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

class InteractiveRegistration:
    def __init__(self, browser_tool: Optional[TestBrowserTool] = None,
                 email_address: Optional[str] = None,
                 email_password: Optional[str] = None,
                 email_provider: str = "gmail",
                 api_key: Optional[str] = None,
                 verification_callback=None):
        self.browser_tool = browser_tool
        self.min_typing_delay = 0.05
        self.max_typing_delay = 0.2
        self.min_action_delay = 0.5
        self.max_action_delay = 2.0
        self.min_page_load_delay = 1.0
        self.max_page_load_delay = 3.0
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
        self.max_retries = 3
        self.current_step = 0

    def _match_keywords(self, text: str, keywords: List[str]) -> bool:
        """检查文本中是否包含任何关键词
        
        Args:
            text: 要检查的文本，可以是None或空字符串
            keywords: 关键词列表
            
        Returns:
            是否匹配任何关键词
        """
        if not text:
            return False
            
        text = text.lower()
        return any(kw.lower() in text for kw in keywords)

    def _build_prompt(self, platform: str, step: int) -> str:
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
    "elements": [
        {{
            "type": "元素类型",
            "description": "元素描述",
            "coordinates": [x, y],
            "is_active": true/false
        }}
    ],
    "suggested_actions": [
        {{
            "type": "操作类型（click/type/select）",
            "target": "操作目标描述",
            "coordinates": [x, y],
            "value": "要输入的值（如果是type操作）"
        }}
    ],
    "next_step": "下一步描述"
}}

注意：
- 所有坐标必须是实际的数字
- 只返回JSON格式，不要附带解释
"""
        return f"分析页面截图，当前步骤: {step}。返回页面类型、元素、建议操作等JSON格式数据。"

    async def _human_delay(self, min_delay=None, max_delay=None):
        await asyncio.sleep(random.uniform(min_delay or self.min_action_delay, max_delay or self.max_action_delay))

    async def _human_typing(self, text: str, coordinates: Tuple[int, int] = None, selector: str = None):
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
                return
            await self._human_delay(0.2, 0.5)
            for char in text:
                if random.random() < 0.05:
                    await self._human_delay(0.5, 1.0)
                await self.browser_tool.type(char)
                if ord(char) > 127:
                    await asyncio.sleep(random.uniform(0.2, 0.4))
                else:
                    await asyncio.sleep(random.uniform(self.min_typing_delay, self.max_typing_delay))
        except Exception as e:
            logger.error(f"输入出错: {e}")

    async def _human_click(self, coordinates=None, selector=None):
        if not self.browser_tool:
            logger.warning("浏览器工具不可用，无法点击")
            return
        try:
            if coordinates:
                x, y = coordinates
                offset_x = random.randint(-5, 5)
                offset_y = random.randint(-5, 5)
                await self.browser_tool.move_mouse(x + offset_x, y + offset_y)
                await self._human_delay(0.1, 0.3)
                await self.browser_tool.page.mouse.click(x, y)
            elif selector:
                if random.random() < 0.3:
                    pos = await self.browser_tool.get_element_position(selector)
                    if pos:
                        x, y = pos
                        await self.browser_tool.move_mouse(x + random.randint(-20, 20), y + random.randint(-20, 20))
                        await self._human_delay(0.1, 0.3)
                await self.browser_tool.click(selector)
        except Exception as e:
            logger.error(f"点击出错: {e}")

    async def _take_screenshot(self, name=None, platform=None) -> str:
        """截取当前页面截图
        
        Args:
            name: 截图名称前缀
            platform: 平台名称
            
        Returns:
            截图路径
        """
        if not self.browser_tool:
            logger.warning("浏览器工具不可用，无法截图")
            return None
            
        try:
            timestamp = int(datetime.now().timestamp())
            name = name or f"{self.current_step}"
            platform_prefix = f"{platform or 'x'}_"
            step_info = f"step{self.current_step}_" if self.current_step > 0 else ""
            
            screenshot_path = f"{self.screenshot_dir}/{platform_prefix}{step_info}{name}_{timestamp}.png"
            
            await self.browser_tool.screenshot(screenshot_path)
            logger.debug(f"截图已保存: {screenshot_path}")
            
            return screenshot_path
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None

    async def _analyze_current_page(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析当前页面，获取页面类型和建议操作
        
        Args:
            context: 上下文信息
            
        Returns:
            分析结果，包含页面类型、建议操作等
        """
        context = context or {}
        platform = context.get("platform", "unknown")
        screenshot_path = await self._take_screenshot(f"analyze_{self.current_step}", platform)
        if not screenshot_path:
            return {"success": False, "error": "截图失败"}
        
        prompt = self._build_prompt(platform, self.current_step)
        
        try:
            result = await analyze_image_with_gpt4_vision(
                image_path=screenshot_path, 
                prompt=prompt, 
                api_key=self.api_key
            )
            
            if "output" in result and "text" in result["output"]:
                import re
                content = result["output"]["text"]
                
                debug_path = os.path.join(self.debug_dir, f"page_analysis_{platform}_{self.current_step}_{os.path.basename(screenshot_path)}.json")
                with open(debug_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "prompt": prompt,
                        "response": content
                    }, f, ensure_ascii=False, indent=2)
                
                json_match = re.search(r'({.*})', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    analysis = json.loads(json_str)
                    analysis["success"] = True
                    logger.debug(f"页面分析结果: {json.dumps(analysis, ensure_ascii=False)}")
                    
                    if "found" in analysis and analysis.get("found") and "coordinates" in analysis:
                        button_text = analysis.get("button_text", "")
                        recommendation = analysis.get("recommendation", "点击按钮")
                        
                        suggested_actions = [{
                            "type": "click",
                            "target": button_text or "检测到的按钮",
                            "coordinates": analysis["coordinates"],
                            "description": recommendation
                        }]
                        
                        analysis["suggested_actions"] = suggested_actions
                        analysis["page_type"] = f"包含按钮 '{button_text}' 的页面"
                        
                        logger.debug(f"已将按钮检测响应转换为页面分析格式，添加了 {len(suggested_actions)} 个建议操作")
                    
                    if "suggested_actions" not in analysis and "plan" not in analysis:
                        page_type = analysis.get("page_type", "").lower()
                        registration_step = analysis.get("registration_step", "").lower()
                        elements = analysis.get("elements", [])
                        
                        suggested_actions = []
                        
                        if self._match_keywords(page_type, ["name", "名称", "创建账号", "create account"]) or self._match_keywords(registration_step, ["name", "名称", "个人信息"]):
                            input_elements = [e for e in elements if e.get("type", "").lower() in ["input", "输入框", "文本框"]]
                            if input_elements:
                                for element in input_elements:
                                    coords = element.get("coordinates")
                                    desc = element.get("description", "").lower()
                                    
                                    if coords:
                                        if self._match_keywords(desc, ["name", "名称", "姓名"]):
                                            suggested_actions.append({
                                                "type": "click",
                                                "target": "名称输入框",
                                                "coordinates": coords
                                            })
                                            suggested_actions.append({
                                                "type": "type",
                                                "target": "输入名称",
                                                "coordinates": coords,
                                                "value": context.get("display_name", "Promora User")
                                            })
                                        elif self._match_keywords(desc, ["email", "邮箱", "电子邮件"]):
                                            suggested_actions.append({
                                                "type": "click",
                                                "target": "邮箱输入框",
                                                "coordinates": coords
                                            })
                                            suggested_actions.append({
                                                "type": "type",
                                                "target": "输入邮箱",
                                                "coordinates": coords,
                                                "value": context.get("email", "test@example.com")
                                            })
                            
                            button_elements = [e for e in elements if e.get("type", "").lower() in ["button", "按钮"]]
                            if button_elements:
                                for button in button_elements:
                                    coords = button.get("coordinates")
                                    desc = button.get("description", "").lower()
                                    
                                    if coords and self._match_keywords(desc, ["next", "下一步", "continue", "继续"]):
                                        suggested_actions.append({
                                            "type": "click",
                                            "target": "下一步按钮",
                                            "coordinates": coords
                                        })
                                        break
                        
                        elif self._match_keywords(page_type, ["birth", "生日", "出生日期"]) or self._match_keywords(registration_step, ["birth", "生日", "出生日期"]):
                            select_elements = [e for e in elements if e.get("type", "").lower() in ["select", "dropdown", "下拉菜单", "选择框"]]
                            if select_elements:
                                for element in select_elements:
                                    coords = element.get("coordinates")
                                    desc = element.get("description", "").lower()
                                    
                                    if coords:
                                        if self._match_keywords(desc, ["month", "月"]):
                                            suggested_actions.append({
                                                "type": "click",
                                                "target": "月份选择框",
                                                "coordinates": coords
                                            })
                                            suggested_actions.append({
                                                "type": "select",
                                                "target": "选择月份",
                                                "coordinates": coords,
                                                "value": context.get("birth_month", "January")
                                            })
                                        elif self._match_keywords(desc, ["day", "日"]):
                                            suggested_actions.append({
                                                "type": "click",
                                                "target": "日期选择框",
                                                "coordinates": coords
                                            })
                                            suggested_actions.append({
                                                "type": "select",
                                                "target": "选择日期",
                                                "coordinates": coords,
                                                "value": context.get("birth_day", "1")
                                            })
                                        elif self._match_keywords(desc, ["year", "年"]):
                                            suggested_actions.append({
                                                "type": "click",
                                                "target": "年份选择框",
                                                "coordinates": coords
                                            })
                                            suggested_actions.append({
                                                "type": "select",
                                                "target": "选择年份",
                                                "coordinates": coords,
                                                "value": context.get("birth_year", "1990")
                                            })
                            
                            button_elements = [e for e in elements if e.get("type", "").lower() in ["button", "按钮"]]
                            if button_elements:
                                for button in button_elements:
                                    coords = button.get("coordinates")
                                    desc = button.get("description", "").lower()
                                    
                                    if coords and self._match_keywords(desc, ["next", "下一步", "continue", "继续"]):
                                        suggested_actions.append({
                                            "type": "click",
                                            "target": "下一步按钮",
                                            "coordinates": coords
                                        })
                                        break
                        
                        if suggested_actions:
                            analysis["suggested_actions"] = suggested_actions
                            logger.debug(f"根据页面类型和注册步骤动态生成了 {len(suggested_actions)} 个建议操作")
                    
                    return analysis
                
                return {"success": False, "error": "无法提取JSON", "raw_response": content}
            
            return {"success": False, "error": "API响应格式不正确", "raw_response": str(result)}
        except Exception as e:
            logger.error(f"分析页面时出错: {e}")
            return {"success": False, "error": str(e)}

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
            max_steps = 12  # 增加最大步骤数以确保能完成注册（原为8步，现为12步）
            
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
                
                current_url = await self.browser_tool.get_current_url()
                url_success = any(path in current_url for path in ["/home", "/explore", "/notifications", "/messages", "/compose/tweet", "/settings", "/i/flow/signup", "/i/flow/login", "/i/flow/single_sign_on"]) or "twitter.com" in current_url or "x.com" in current_url
                
                keywords_success = self._match_keywords(page_type, ["完成", "成功", "完成注册", "注册成功", "home", "timeline", "feed", "主页", "时间线"])
                
                element_success = await self.browser_tool.element_exists("div[data-testid='primaryColumn']", timeout=2000)
                

                home_elements = [
                    "div[data-testid='AppTabBar_Home_Link']",
                    "div[data-testid='SideNav_NewTweet_Button']",
                    "a[aria-label='Profile']",
                    "div[aria-label='Home timeline']",
                    "div[aria-label='主页时间线']",
                    "div[data-testid='primaryColumn']",
                    "div[data-testid='tweet']",
                    "div[data-testid='tweetText']",
                    "div[aria-label='Timeline: Your Home Timeline']",
                    "div[aria-label='时间线：你的主页时间线']",
                    "div[data-testid='ScrollSnap-List']",
                    "div[data-testid='signupButton']",
                    "div[data-testid='loginButton']"
                ]
                home_element_exists = False
                for element in home_elements:
                    if await self.browser_tool.element_exists(element, timeout=1000):
                        logger.info(f"检测到X主页元素: {element}")
                        home_element_exists = True
                        break
                
                if url_success or keywords_success or element_success or home_element_exists:
                    logger.info("注册完成! 检测到X主页界面")
                    logger.info(f"URL检查: {'成功' if url_success else '失败'}, 当前URL: {current_url}")
                    logger.info(f"关键词检查: {'成功' if keywords_success else '失败'}, 页面类型: {page_type}")
                    logger.info(f"元素检查: {'成功' if element_success else '失败'}")
                    logger.info(f"主页元素检查: {'成功' if home_element_exists else '失败'}")
                    
                    await self._human_delay(5.0, 8.0)
                    
                    timestamp = int(datetime.now().timestamp())
                    
                    tmp_success_path = f"/tmp/x_registration_success.png"
                    await self.browser_tool.screenshot(tmp_success_path)
                    logger.info(f"保存成功截图到临时目录: {tmp_success_path}")
                    
                    final_success_path = f"/tmp/final_success_screenshot.png"
                    await self.browser_tool.screenshot(final_success_path)
                    logger.info(f"保存最终成功截图: {final_success_path}")
                    
                    final_screenshot = await self._take_screenshot(f"success_final_{username}", "x")
                    logger.info(f"保存最终成功界面截图: {final_screenshot}")
                    
                    success_path = f"{self.screenshot_dir}/x_registration_success_{username}_{timestamp}.png"
                    await self.browser_tool.screenshot(success_path)
                    logger.info(f"额外保存成功界面截图: {success_path}")
                    
                    await self._human_delay(3.0, 5.0)
                    extra_screenshot = await self._take_screenshot(f"success_extra_{username}", "x")
                    logger.info(f"保存额外成功界面截图: {extra_screenshot}")
                    
                    account = PlatformAccount(
                        account_id=f"x_{username.lower()}_{int(time.time())}",
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
                            action["value"] = str(random.randint(1980, 2000))
                        elif "month" in target or "月" in target:
                            action["value"] = str(random.randint(1, 12))
                        elif "day" in target or "日" in target:
                            action["value"] = str(random.randint(1, 28))
                
                success = await self._execute_suggested_actions(suggested_actions)
                if not success:
                    logger.warning(f"执行操作失败，步骤 {self.current_step}")
                    
                    if self.current_step > 1:  # 不在第一步重试
                        retry_screenshot = await self._take_screenshot(f"retry_action_{self.current_step}")
                        logger.debug(f"重试截图: {retry_screenshot}")
                        await self._human_delay(2.0, 3.0)
                        continue
                    else:
                        return None
                
                await self._human_delay(1.0, 2.0)
                self.current_step += 1
            
            logger.warning(f"达到最大步骤数 {max_steps}，检查是否已经成功")
            
            current_url = await self.browser_tool.get_current_url()
            url_success = any(path in current_url for path in ["/home", "/explore", "/notifications", "/messages", "/compose/tweet", "/settings", "/i/flow/signup", "/i/flow/login", "/i/flow/single_sign_on"]) or "twitter.com" in current_url or "x.com" in current_url
            
            success_indicators = [
                "div[data-testid='primaryColumn']",
                "div[data-testid='AppTabBar_Home_Link']",
                "div[data-testid='SideNav_NewTweet_Button']",
                "a[aria-label='Profile']",
                "div[aria-label='Home timeline']",
                "div[aria-label='主页时间线']",
                "div[data-testid='tweetButtonInline']",
                "div[data-testid='tweetButton']",
                "div[data-testid='cellInnerDiv']"
            ]
            
            success_detected = False
            for indicator in success_indicators:
                if await self.browser_tool.element_exists(indicator, timeout=1000):
                    logger.info(f"检测到成功指标: {indicator}")
                    success_detected = True
                    break
                    
            if success_detected or url_success:
                logger.info("检测到X主页界面，注册可能已经成功")
                logger.info(f"URL检查: {'成功' if url_success else '失败'}, 当前URL: {current_url}")
                logger.info(f"元素检查: {'成功' if success_detected else '失败'}")
                
                await self._human_delay(5.0, 8.0)
                
                timestamp = int(datetime.now().timestamp())
                
                tmp_success_path = f"/tmp/x_registration_success.png"
                await self.browser_tool.screenshot(tmp_success_path)
                logger.info(f"保存成功截图到临时目录: {tmp_success_path}")
                
                final_success_path = f"/tmp/final_success_screenshot.png"
                await self.browser_tool.screenshot(final_success_path)
                logger.info(f"保存最终成功截图: {final_success_path}")
                
                final_screenshot = await self._take_screenshot(f"final_check_success_{username}", "x")
                logger.info(f"保存最终成功界面截图: {final_screenshot}")
                
                await self._human_delay(3.0, 5.0)
                extra_screenshot = await self._take_screenshot(f"final_extra_success_{username}", "x")
                logger.info(f"保存额外成功界面截图: {extra_screenshot}")
                
                account = PlatformAccount(
                    account_id=f"x_{username.lower()}_{int(time.time())}",
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
                
                account_path = f"{self.screenshot_dir}/x_account_{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
                with open(account_path, "w", encoding="utf-8") as f:
                    json.dump(account.dict(), f, ensure_ascii=False, indent=2, default=str)
                logger.info(f"保存账户信息: {account_path}")
                
                return account
            
            logger.warning("注册未完成")
            return None
            
        except Exception as e:
            logger.error(f"注册过程中出错: {e}")
            logger.error(traceback.format_exc())
            
            try:
                error_screenshot = await self._take_screenshot(f"error_{username}")
                logger.debug(f"错误状态截图: {error_screenshot}")
            except Exception as screenshot_error:
                logger.error(f"无法保存错误状态截图: {screenshot_error}")
                
            return None

async def notification_callback(message, verification_data):
    """验证通知回调函数
    
    Args:
        message: 通知消息
        verification_data: 验证数据
    """
    logger.info(f"需要验证: {message}")
    logger.info(f"验证ID: {verification_data['id']}")
    logger.info(f"验证类型: {verification_data['type']}")
    logger.info(f"验证详情: {verification_data['details']}")
    
    if verification_data.get('screenshot'):
        logger.info(f"验证截图: {verification_data['screenshot']}")
    
    if verification_data['type'] == 'email':
        verification_code = input(f"请输入邮箱验证码 (验证ID: {verification_data['id']}): ")
        await handle_verification_challenge(verification_data['id'], verification_code)
    elif verification_data['type'] == 'captcha':
        verification_code = input(f"请输入图形验证码 (验证ID: {verification_data['id']}): ")
        await handle_verification_challenge(verification_data['id'], verification_code)

async def handle_verification_challenge(verification_id, verification_code=None):
    """处理验证挑战
    
    Args:
        verification_id: 验证ID
        verification_code: 验证码，如果为None则提示用户输入
        
    Returns:
        是否成功处理验证挑战
    """
    logger.debug(f"处理验证挑战: ID={verification_id}")
    if verification_code is None:
        verification_code = input(f"请输入验证码 (验证ID: {verification_id}): ")
    
    result = {
        "code": verification_code,
        "action": "submit"
    }
    
    logger.debug(f"提交验证结果: {result}")
    success = await VerificationDialog.submit_verification_result(
        verification_id=verification_id,
        result=result
    )
    
    logger.debug(f"验证结果处理状态: {'成功' if success else '失败'}")
    return success

async def test_interactive_x_registration(args):
    """测试交互式LLM引导的X账户注册
    
    Args:
        args: 命令行参数
    
    Returns:
        注册成功的账户信息，失败则返回None
    """
    debug_dir = Path("/tmp/promora_interactive_x_registration")
    debug_dir.mkdir(exist_ok=True)
    
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    email = args.email or f"test.{random_str}@promora.ai"
    password = args.password or ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=12))
    username = args.username or "PromoraAI"  # 默认使用指定的用户名
    display_name = args.display_name or f"Promora AI {random.randint(100, 999)}"
    
    logger.info(f"开始测试交互式LLM引导的X账户注册: {username} / {email}")
    logger.info(f"使用的密码: {password}")
    
    browser_tool = TestBrowserTool(
        headless=not args.show_browser,  # 根据参数决定是否显示浏览器窗口
        slow_mo=args.slow_mo,
        timeout=args.timeout,
        screenshot_dir=str(debug_dir)
    )
    
    try:
        logger.info("启动浏览器...")
        await browser_tool.start()
        
        initial_screenshot = f"{debug_dir}/initial_browser_{int(datetime.now().timestamp())}.png"
        await browser_tool.screenshot(initial_screenshot)
        logger.debug(f"初始浏览器截图: {initial_screenshot}")
        
        email_address = args.email_address or os.environ.get("EMAIL_ADDRESS")
        email_password = args.email_password or os.environ.get("EMAIL_PASSWORD")
        email_provider = args.email_provider or os.environ.get("EMAIL_PROVIDER", "gmail")
        
        if not email_address or not email_password:
            logger.warning("未设置邮箱凭据，将无法自动处理邮箱验证")
            logger.info("请设置以下环境变量或通过命令行参数提供:")
            logger.info("  EMAIL_ADDRESS: 用于接收验证邮件的邮箱地址")
            logger.info("  EMAIL_PASSWORD: 邮箱密码")
            logger.info("  EMAIL_PROVIDER: 邮箱提供商（默认为gmail）")
        else:
            logger.debug(f"使用邮箱: {email_address} ({email_provider})")
        
        api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("未设置OpenAI API密钥，将使用模拟的LLM引导功能")
            api_key = "sk-mock-key"
        
        interactive_registration = InteractiveRegistration(
            browser_tool=browser_tool,
            email_address=email_address,
            email_password=email_password,
            email_provider=email_provider,
            api_key=api_key,
            verification_callback=notification_callback
        )
        
        interactive_registration.screenshot_dir = str(debug_dir)
        
        logger.info(f"开始注册X账户: {username} / {email}")
        
        account = await interactive_registration.register_x_account(
            username=username,
            email=email,
            password=password,
            display_name=display_name
        )
        
        if account:
            logger.info(f"X账户注册成功: {account.username}")
            
            account_file = debug_dir / f"x_account_{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            with open(account_file, "w", encoding="utf-8") as f:
                json.dump(account.dict(), f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"账户信息已保存到: {account_file}")
            
            return account
        else:
            logger.warning("X账户注册失败")
            
            final_screenshot = f"{debug_dir}/final_state_{int(datetime.now().timestamp())}.png"
            await browser_tool.screenshot(final_screenshot)
            logger.debug(f"最终页面状态截图: {final_screenshot}")
            
            return None
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        logger.error(traceback.format_exc())
        
        error_screenshot = f"{debug_dir}/error_state_{int(datetime.now().timestamp())}.png"
        try:
            await browser_tool.screenshot(error_screenshot)
            logger.debug(f"错误状态截图: {error_screenshot}")
        except:
            logger.error("无法截取错误状态截图")
        
        raise
    finally:
        logger.info("关闭浏览器...")
        await browser_tool.close()

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="交互式LLM引导的X账户注册测试")
    
    parser.add_argument("--username", help="X用户名", default="PromoraAI")
    parser.add_argument("--email", help="注册邮箱")
    parser.add_argument("--password", help="账户密码")
    parser.add_argument("--display-name", help="显示名称")
    
    parser.add_argument("--email-address", help="用于接收验证码的邮箱地址")
    parser.add_argument("--email-password", help="邮箱密码")
    parser.add_argument("--email-provider", help="邮箱提供商", default="gmail")
    
    parser.add_argument("--api-key", help="OpenAI API密钥")
    
    parser.add_argument("--show-browser", action="store_true", help="显示浏览器窗口")
    parser.add_argument("--slow-mo", type=int, default=100, help="操作之间的延迟（毫秒）")
    parser.add_argument("--timeout", type=int, default=60000, help="默认超时时间（毫秒）")
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(test_interactive_x_registration(args))
