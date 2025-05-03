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
from services.vision_llm import analyze_image_with_gpt4_vision

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
        if not text:
            return False
        text = text.lower()
        return any(kw.lower() in text for kw in keywords)

    def _build_prompt(self, platform: str, step: int, context: dict = None) -> str:
        self.context = context or {}
        return f"""
你是一位网页注册助手，任务是根据截图中的网页结构和用户提供的注册信息，制定一整套自动化注册操作流程。

---

📸 页面截图：你将看到的是X注册页面的截图，当前步骤: {step}。

📋 用户提供的注册信息如下：
{{
  "username": "{self.context.get('username', 'promoraai')}",
  "email": "{self.context.get('email', 'test@promora.ai')}",
  "password": "{self.context.get('password', 'P@ssw0rd')}",
  "display_name": "{self.context.get('display_name', 'Promora AI')}"
}}

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
      "value": "{self.context.get('username', 'promoraai')}"
    }},
    {{
      "step": 3,
      "type": "click",
      "description": "点击 'Next' 按钮",
      "coordinates": [500, 600],
      "value": null
    }}
  ],
  "human_simulation": {{
    "typing_speed": "variable",
    "pause_between_actions": true,
    "mouse_movement": "natural",
    "action_sequence": "click_then_type"
  }},
  "final_remark": "完成后应该跳转到下一个页面"
}}
"""

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
        context = context or {}
        platform = context.get("platform", "unknown")
        screenshot_path = await self._take_screenshot(f"analyze_{self.current_step}", platform)
        if not screenshot_path:
            return {"success": False, "error": "截图失败"}

        prompt = self._build_prompt(platform, self.current_step, context)

        try:
            result = await analyze_image_with_gpt4_vision(
                image_path=screenshot_path,
                prompt=prompt,
                api_key=self.api_key
            )
            if "output" in result and "text" in result["output"]:
                import re
                content = result["output"]["text"]
                json_match = re.search(r'({.*})', content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group(1))
                    analysis["success"] = True
                    return analysis
                else:
                    return {"success": False, "error": "无法提取JSON", "raw_response": content}
            else:
                return {"success": False, "error": "API响应格式不正确", "raw_response": str(result)}
        except Exception as e:
            logger.error(f"分析页面时出错: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_suggested_actions(self, actions: List[Dict[str, Any]]) -> bool:
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
        if any(keyword in page_type for keyword in ["验证", "verification", "captcha", "code", "邮箱", "email"]):
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
                timeout=300
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

                    submit_buttons = [e for e in analysis.get("elements", []) if e.get("type", "").lower() in ["button", "按钮"]
                                      and any(k in e.get("description", "").lower() for k in ["submit", "verify", "确认", "验证", "登录", "next", "继续"])]
                    if submit_buttons:
                        await self._human_click(coordinates=submit_buttons[0].get("coordinates"))
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
        if not self.browser_tool:
            logger.error("浏览器工具不可用，无法注册X账户")
            return None

        display_name = display_name or f"{username.capitalize()} User"

        context = {
            "platform": "x",
            "task": "注册X账户",
            "username": username,
            "email": email,
            "display_name": display_name,
            "birth_year": str(random.randint(1975, 2000)),
            "birth_month": str(random.randint(1, 12)),
            "birth_day": str(random.randint(1, 28)),
            "password": password
        }

        try:
            logger.info("导航到X注册页面...")
            await self.browser_tool.navigate("https://twitter.com/i/flow/signup")
            await self._human_delay(self.min_page_load_delay, self.max_page_load_delay)

            self.current_step = 1
            max_steps = 15  # 允许更长的注册流程处理

            while self.current_step <= max_steps:
                logger.info(f"执行注册步骤 {self.current_step}...")

                # 提前处理“Use email instead”
                if await self.browser_tool.element_exists("text=Use email instead"):
                    logger.info("点击 'Use email instead' 按钮...")
                    await self._human_click(selector="text=Use email instead")
                    await self._human_delay(0.5, 1.0)

                analysis = await self._analyze_current_page(context)

                if not analysis.get("success", False):
                    logger.warning(f"分析页面失败: {analysis.get('error')}")
                    if self.current_step > 1:
                        await self._human_delay(1.0, 2.0)
                        self.current_step += 1
                        continue
                    return None

                # 检测验证码页面
                if self._match_keywords(analysis.get("page_type", ""), ["验证", "verification", "code", "captcha"]):
                    logger.info("检测到验证码页面，进入验证处理流程...")
                    verified = await self._handle_verification("x", username)
                    if not verified:
                        logger.error("验证码处理失败")
                        return None
                    self.current_step += 1
                    continue

                # 判断是否已完成注册
                current_url = await self.browser_tool.get_current_url()
                if any(path in current_url for path in ["/home", "/explore", "/notifications", "/compose/tweet"]):
                    logger.info(f"注册成功！跳转到了主页: {current_url}")
                    break

                suggested_actions = analysis.get("suggested_actions", [])
                for action in suggested_actions:
                    if action["type"] == "type" and not action.get("value"):
                        target = action.get("target", "").lower()
                        if "name" in target:
                            action["value"] = display_name
                        elif "email" in target:
                            action["value"] = email
                        elif "user" in target:
                            action["value"] = username
                        elif "password" in target:
                            action["value"] = password
                        elif "year" in target:
                            action["value"] = context.get("birth_year")
                        elif "month" in target:
                            action["value"] = context.get("birth_month")
                        elif "day" in target:
                            action["value"] = context.get("birth_day")

                if suggested_actions:
                    success = await self._execute_suggested_actions(suggested_actions)
                    if not success:
                        logger.warning("部分操作执行失败，尝试跳过当前步骤")
                else:
                    logger.warning("没有检测到建议操作，自动尝试点击下一步")
                    if await self.browser_tool.element_exists("text=Next"):
                        await self._human_click(selector="text=Next")
                        await self._human_delay(0.5, 1.0)

                await self._human_delay(1.0, 2.0)
                self.current_step += 1

            logger.info("注册流程结束，检测是否成功进入主页")
            final_url = await self.browser_tool.get_current_url()
            if any(path in final_url for path in ["/home", "/explore"]):
                logger.info("确认成功进入X主页")

                account = PlatformAccount(
                    account_id=f_

import argparse

async def test_interactive_x_registration():
    parser = argparse.ArgumentParser(description="使用LLM自动注册X账户")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--display-name", default=None)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--show-browser", action="store_true")
    args = parser.parse_args()

    browser_tool = TestBrowserTool(headless=not args.show_browser)
    await browser_tool.start()

    registration = InteractiveRegistration(
        browser_tool=browser_tool,
        api_key=args.api_key,
        verification_callback=None  # 可设置为自定义处理验证码函数
    )

    account = await registration.register_x_account(
        username=args.username,
        email=args.email,
        password=args.password,
        display_name=args.display_name
    )

    if account:
        print(f"✅ 注册成功: {account.username}")
    else:
        print("❌ 注册失败")

    await browser_tool.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_interactive_x_registration())
