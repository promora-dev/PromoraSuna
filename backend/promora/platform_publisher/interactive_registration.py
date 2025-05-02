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
import re
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
        if not text:
            return False
            
        text = text.lower()
        pattern = '|'.join(re.escape(kw.lower()) for kw in keywords)
        return bool(re.search(pattern, text))
        
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
                offset_x = random.randint(-3, 3)
                offset_y = random.randint(-3, 3)
                await self.browser_tool.move_mouse(x + offset_x, y + offset_y)
                await self._human_delay(0.1, 0.3)
                await self.browser_tool.page.mouse.click(x, y)
            elif selector:
                await self.browser_tool.click(selector)
            else:
                logger.warning("未提供输入框坐标或选择器，无法点击输入框")
                return
                
            await self._human_delay(0.2, 0.5)
            
            if random.random() < 0.3:  # 有时候会先清空输入框
                await self.browser_tool.press("Control+a")
                await self._human_delay(0.1, 0.2)
                await self.browser_tool.press("Backspace")
                await self._human_delay(0.2, 0.4)
            
            for char in text:
                if random.random() < 0.08:  # 增加停顿概率
                    await self._human_delay(0.5, 1.2)
                
                await self.browser_tool.type(char)
                
                if ord(char) > 127:
                    await asyncio.sleep(random.uniform(0.3, 0.5))  # 增加中文输入延迟
                elif char in ".,;:!?()[]{}\"'":
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                elif char.isdigit():
                    await asyncio.sleep(random.uniform(0.03, 0.15))
                else:
                    await asyncio.sleep(random.uniform(self.min_typing_delay, self.max_typing_delay))
                
                if len(text) > 5 and random.random() < 0.03:
                    await self._human_delay(0.1, 0.2)
                    await self.browser_tool.press("Backspace")
                    await self._human_delay(0.2, 0.4)
                    await self.browser_tool.type(char)
                    await asyncio.sleep(random.uniform(0.1, 0.2))
                
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
                
                offset_x = random.randint(-8, 8)
                offset_y = random.randint(-8, 8)
                
                await self.browser_tool.move_mouse(x + offset_x * 2, y + offset_y * 2)
                await self._human_delay(0.1, 0.2)
                await self.browser_tool.move_mouse(x + offset_x, y + offset_y)
                await self._human_delay(0.05, 0.15)
                
                await self.browser_tool.page.mouse.click(x, y)
                logger.debug(f"点击坐标: ({x}, {y})")
                
            elif selector:
                if random.random() < 0.4:  # 增加概率
                    element_pos = await self.browser_tool.get_element_position(selector)
                    if element_pos:
                        x, y = element_pos
                        
                        offset_x = random.randint(-25, 25)
                        offset_y = random.randint(-25, 25)
                        
                        await self.browser_tool.move_mouse(x + offset_x * 2, y + offset_y * 2)
                        await self._human_delay(0.1, 0.2)
                        await self.browser_tool.move_mouse(x + offset_x, y + offset_y)
                        await self._human_delay(0.1, 0.2)
                        await self.browser_tool.move_mouse(x, y)
                        await self._human_delay(0.05, 0.1)
                
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
            step_info = f"step{self.current_step}_" if self.current_step > 0 else ""
            
            screenshot_path = f"{self.screenshot_dir}/{platform_prefix}{step_info}{name}_{timestamp}.png"
            
            await self.browser_tool.screenshot(screenshot_path)
            logger.debug(f"截图已保存: {screenshot_path}")
            
            return screenshot_path
        except Exception as e:
            logger.error(f"截取截图时出错: {e}")
            return None
    
    def _build_prompt(self, platform: str, step: int, context: Dict[str, Any] = None) -> str:
        """构建LLM分析提示词
        
        Args:
            platform: 平台名称
            step: 当前步骤
            context: 上下文信息，包含注册信息等
            
        Returns:
            提示词
        """
        context = context or {}
        
        username = context.get("username", "")
        email = context.get("email", "")
        display_name = context.get("display_name", "")
        password = context.get("password", "")
        birth_year = context.get("birth_year", str(random.randint(1970, 2000)))
        birth_month = context.get("birth_month", random.choice(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]))
        birth_day = context.get("birth_day", str(random.randint(1, 28)))
        
        registration_json = {
            "username": username,
            "email": email,
            "password": password,
            "display_name": display_name,
            "birth_year": birth_year,
            "birth_month": birth_month,
            "birth_day": birth_day
        }
        
        registration_info = f"""
📋 用户提供的注册信息如下：
{json.dumps(registration_json, ensure_ascii=False, indent=2)}
"""

        base_prompt = f"""
你是一位网页注册助手，任务是根据截图中的网页结构和用户提供的注册信息，制定一整套自动化注册操作流程。

---

📸 页面截图：你将看到的是一个注册页面的截图，当前步骤: {step}。

{registration_info}

---

请根据截图中呈现的页面结构、字段提示、按钮文本，分析并返回一个完整的 JSON 结构，描述应该如何填写和点击这些元素，模拟人类操作流程。

输出格式如下：

{{
  "page_type": "页面类型，例如：填写信息页、生日选择页、验证码页",
  "plan": [
    {{
      "step": 1,
      "type": "click | type | select",
      "description": "点击 Name 输入框",
      "target_hint": "输入框上方或内部提示为 'Name' 或类似",
      "coordinates": [120, 280],
      "value": null
    }},
    {{
      "step": 2,
      "type": "type",
      "description": "输入用户名",
      "coordinates": [120, 280],
      "value": "{username}"
    }},
    {{
      "step": 3,
      "type": "click",
      "description": "点击 'Next' 按钮",
      "coordinates": [500, 600],
      "value": null
    }}
  ],
  "final_remark": "完成后应该跳转到验证码页面，等待验证码输入"
}}

⚠️ 要求：
- 按照用户输入内容合理匹配界面字段
- 不遗漏任何用户输入需要填写的内容
- 保证每个字段填写前先点击，再输入（模拟人类行为）
- 所有坐标使用实际数字
- 只返回 JSON，不要多余解释或 markdown
- 操作间隔时间应该模拟真实人类行为，避免机械固定的间隔
- 对于输入操作，考虑真实人类的打字速度和可能的错误修正
"""

        if platform == "x":
            return f"""
你是一位网页注册助手，任务是根据截图中的X（Twitter）注册页面结构和用户提供的注册信息，制定一整套自动化注册操作流程。

---

📸 页面截图：你将看到的是X（Twitter）注册页面的截图，当前步骤: {step}。

{registration_info}

---

请根据截图中呈现的页面结构、字段提示、按钮文本，分析并返回一个完整的 JSON 结构，描述应该如何填写和点击这些元素，模拟人类操作流程。

输出格式如下：

{{
  "page_type": "页面类型，例如：填写信息页、生日选择页、验证码页",
  "plan": [
    {{
      "step": 1,
      "type": "click | type | select",
      "description": "点击 Name 输入框",
      "target_hint": "输入框上方或内部提示为 'Name' 或类似",
      "coordinates": [120, 280],
      "value": null,
      "duration": 0.8
    }},
    {{
      "step": 2,
      "type": "type",
      "description": "输入用户名",
      "coordinates": [120, 280],
      "value": "{display_name}",
      "duration": 1.2
    }},
    {{
      "step": 3,
      "type": "click",
      "description": "点击 'Next' 按钮",
      "coordinates": [500, 600],
      "value": null,
      "duration": 0.5
    }}
  ],
  "final_remark": "完成后应该跳转到验证码页面，等待验证码输入",
  "human_simulation": {{
    "typing_speed": "正常",
    "mouse_movement": "自然",
    "overall_pace": "正常"
  }}
}}

⚠️ 要求：
- 按照用户输入内容合理匹配界面字段
- 不遗漏任何用户输入需要填写的内容
- 保证每个字段填写前先点击，再输入（模拟人类行为）
- 所有坐标使用实际数字
- 只返回 JSON，不要多余解释或 markdown
- 如果看到"Use email instead"按钮，请将其作为第一个步骤
- 对于生日选择，请确保年份在2000年之前，避免年龄限制问题
- 操作间隔时间应该模拟真实人类行为，避免机械固定的间隔
- 对于输入操作，考虑真实人类的打字速度和可能的错误修正
- 如果是输入名称字段，请只使用显示名称，不要混入邮箱或其他信息
"""
        elif platform == "zhihu":
            return f"""
你是一位网页注册助手，任务是根据截图中的知乎注册/登录页面结构和用户提供的注册信息，制定一整套自动化注册操作流程。

---

📸 页面截图：你将看到的是知乎注册/登录页面的截图，当前步骤: {step}。

{registration_info}

---

请根据截图中呈现的页面结构、字段提示、按钮文本，分析并返回一个完整的 JSON 结构，描述应该如何填写和点击这些元素，模拟人类操作流程。

输出格式如下：

{{
  "page_type": "页面类型，例如：登录页、注册页、验证码页",
  "plan": [
    {{
      "step": 1,
      "type": "click | type | select | drag",
      "description": "点击手机号输入框",
      "target_hint": "输入框上方或内部提示为'手机号'或类似",
      "coordinates": [120, 280],
      "value": null,
      "duration": 0.8
    }},
    {{
      "step": 2,
      "type": "type",
      "description": "输入手机号",
      "coordinates": [120, 280],
      "value": "{email}",
      "duration": 1.2
    }},
    {{
      "step": 3,
      "type": "click",
      "description": "点击'获取验证码'按钮",
      "coordinates": [500, 600],
      "value": null,
      "duration": 0.5
    }}
  ],
  "final_remark": "完成后应该等待验证码",
  "human_simulation": {{
    "typing_speed": "正常",
    "mouse_movement": "自然",
    "overall_pace": "正常"
  }}
}}

⚠️ 要求：
- 按照用户输入内容合理匹配界面字段
- 不遗漏任何用户输入需要填写的内容
- 保证每个字段填写前先点击，再输入（模拟人类行为）
- 所有坐标使用实际数字
- 只返回 JSON，不要多余解释或 markdown
- 如果看到滑动验证码，请提供滑块起始坐标和目标坐标
- 操作间隔时间应该模拟真实人类行为，避免机械固定的间隔
- 对于输入操作，考虑真实人类的打字速度和可能的错误修正
"""
        
        return base_prompt
    
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
        
        prompt = self._build_prompt(platform, self.current_step, context)
        
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
            actions: 操作列表（可以是旧格式的suggested_actions或新格式的plan）
            
        Returns:
            是否成功执行所有操作
        """
        if not actions:
            logger.warning("没有建议的操作")
            return False
        
        is_plan_format = "step" in actions[0] if actions else False
        
        for action in actions:
            action_type = action.get("type", "").lower()
            description = action.get("description", "") or action.get("target", "")
            coordinates = action.get("coordinates")
            value = action.get("value")
            selector = action.get("selector")
            duration = action.get("duration", None)
            
            logger.debug(f"执行操作: {action_type} - {description}")
            
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
                    wait_time = duration or action.get("duration", 2)
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
                elif action_type == "drag":
                    start_coordinates = action.get("start_coordinates")
                    end_coordinates = action.get("end_coordinates") or coordinates
                    if start_coordinates and end_coordinates:
                        await self.browser_tool.drag_and_drop(
                            start_x=start_coordinates[0], 
                            start_y=start_coordinates[1],
                            end_x=end_coordinates[0],
                            end_y=end_coordinates[1]
                        )
                    else:
                        logger.warning(f"无法执行拖动操作，未提供起始或结束坐标: {action}")
                        continue
                else:
                    logger.warning(f"未知操作类型: {action_type}")
                    continue
                
                if duration is not None:
                    await asyncio.sleep(duration)
                else:
                    await self._human_delay()
                
            except Exception as e:
                logger.error(f"执行操作时出错: {action_type} - {description} - {e}")
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
            "password": password,  # 添加密码到上下文
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
                    
                    final_screenshot = await self._take_screenshot(f"success_final_{username}", "x")
                    logger.info(f"保存最终成功界面截图: {final_screenshot}")
                    
                    success_path = f"/tmp/promora_interactive_x_registration/x_registration_success_{username}_{int(datetime.now().timestamp())}.png"
                    await self.browser_tool.screenshot(success_path)
                    logger.info(f"额外保存成功界面截图: {success_path}")
                    
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
                    
                    account_path = f"/tmp/promora_interactive_x_registration/x_account_{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
                    with open(account_path, "w", encoding="utf-8") as f:
                        json.dump(account.to_dict(), f, ensure_ascii=False, indent=2)
                    logger.info(f"保存账户信息: {account_path}")
                    
                    return account
                
                plan = analysis.get("plan", [])
                suggested_actions = analysis.get("suggested_actions", [])
                
                actions = plan if plan else suggested_actions
                
                field_types = {}
                
                for action in actions:
                    if action.get("type") == "type":
                        description = action.get("description", "") or action.get("target", "")
                        description = description.lower()
                        coordinates = action.get("coordinates")
                        
                        if coordinates:
                            if self._match_keywords(description, ["name", "名称", "display", "姓名"]) and not self._match_keywords(description, ["email", "邮箱", "电子邮件"]):
                                field_types[str(coordinates)] = "name"
                                logger.debug(f"识别到名称字段: {description}, 坐标: {coordinates}")
                            elif self._match_keywords(description, ["email", "邮箱", "电子邮件"]):
                                field_types[str(coordinates)] = "email"
                                logger.debug(f"识别到邮箱字段: {description}, 坐标: {coordinates}")
                            elif self._match_keywords(description, ["user", "用户名"]):
                                field_types[str(coordinates)] = "username"
                                logger.debug(f"识别到用户名字段: {description}, 坐标: {coordinates}")
                            elif self._match_keywords(description, ["password", "密码"]):
                                field_types[str(coordinates)] = "password"
                                logger.debug(f"识别到密码字段: {description}, 坐标: {coordinates}")
                
                for action in actions:
                    if action.get("type") == "type" and not action.get("value"):
                        description = action.get("description", "") or action.get("target", "")
                        description = description.lower()
                        coordinates = action.get("coordinates")
                        coords_str = str(coordinates) if coordinates else ""
                        
                        if coords_str and coords_str in field_types:
                            field_type = field_types[coords_str]
                            if field_type == "name":
                                action["value"] = display_name
                                logger.info(f"填充名称字段: {display_name}")
                            elif field_type == "email":
                                action["value"] = email
                                logger.info(f"填充邮箱字段: {email}")
                            elif field_type == "username":
                                action["value"] = username
                                logger.info(f"填充用户名字段: {username}")
                            elif field_type == "password":
                                action["value"] = password
                                logger.info(f"填充密码字段: {password}")
                        elif self._match_keywords(description, ["name", "名称", "display", "姓名"]) and not self._match_keywords(description, ["email", "邮箱", "电子邮件"]):
                            action["value"] = display_name
                            logger.info(f"通过描述填充名称字段: {display_name}")
                        elif self._match_keywords(description, ["email", "邮箱", "电子邮件"]):
                            action["value"] = email
                            logger.info(f"通过描述填充邮箱字段: {email}")
                        elif self._match_keywords(description, ["user", "用户名"]):
                            action["value"] = username
                            logger.info(f"填充用户名字段: {username}")
                        elif self._match_keywords(description, ["password", "密码"]):
                            action["value"] = password
                            logger.info(f"填充密码字段: {password}")
                        elif self._match_keywords(description, ["year", "年"]):
                            action["value"] = str(random.randint(1970, 2000))  # 随机年份
                            logger.info(f"填充年份字段: {action['value']}")
                        elif self._match_keywords(description, ["month", "月"]):
                            action["value"] = str(random.randint(1, 12))  # 随机月份
                            logger.info(f"填充月份字段: {action['value']}")
                        elif self._match_keywords(description, ["day", "日"]):
                            action["value"] = str(random.randint(1, 28))  # 随机日期
                            logger.info(f"填充日期字段: {action['value']}")
                
                if not actions:
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
