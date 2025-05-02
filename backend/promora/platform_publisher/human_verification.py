"""
人工验证辅助模块

此模块提供了一个人工验证辅助类，用于在自动化过程中需要人工干预时提供帮助。
"""

import os
import asyncio
import logging
import random
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Callable, Awaitable

logger = logging.getLogger("agentpress")

class HumanVerificationAssistant:
    """人工验证辅助类，用于处理需要人工干预的验证挑战"""
    
    def __init__(
        self, 
        browser_tool: Any, 
        platform: str,
        account_id: str,
        debug_dir: Optional[str] = None,
        callback_url: Optional[str] = None,
        notification_callback: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None
    ):
        """初始化人工验证辅助类
        
        Args:
            browser_tool: 浏览器工具实例
            platform: 平台名称
            account_id: 账户ID
            debug_dir: 调试信息保存目录
            callback_url: 回调URL，用于通知验证完成
            notification_callback: 通知回调函数
        """
        self.browser_tool = browser_tool
        self.platform = platform
        self.account_id = account_id
        self.debug_dir = Path(debug_dir) if debug_dir else Path("/tmp/promora_verification")
        self.debug_dir.mkdir(exist_ok=True)
        self.callback_url = callback_url
        self.notification_callback = notification_callback
        self.verification_id = f"{platform}_{account_id}_{int(datetime.now().timestamp())}"
        self.verification_status = "pending"
        self.verification_data = {}
        
    async def handle_verification(
        self, 
        verification_type: str,
        verification_details: Dict[str, Any],
        timeout: int = 300,
        retry_interval: int = 5
    ) -> Tuple[bool, Dict[str, Any]]:
        """处理验证挑战
        
        Args:
            verification_type: 验证类型（如"captcha", "sms", "email"等）
            verification_details: 验证详情
            timeout: 超时时间（秒）
            retry_interval: 重试间隔（秒）
            
        Returns:
            (成功标志, 验证结果数据)
        """
        logger.info(f"开始处理{self.platform}平台的{verification_type}验证")
        
        self.verification_status = "waiting_for_human"
        self.verification_data = {
            "id": self.verification_id,
            "platform": self.platform,
            "account_id": self.account_id,
            "type": verification_type,
            "details": verification_details,
            "status": self.verification_status,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "result": None
        }
        
        self._save_verification_data()
        
        screenshot_path = await self._take_verification_screenshot(verification_type)
        self.verification_data["screenshot"] = screenshot_path
        self._save_verification_data()
        
        if self.notification_callback:
            await self.notification_callback(
                f"{self.platform}平台需要人工验证", 
                {
                    "verification_id": self.verification_id,
                    "verification_type": verification_type,
                    "screenshot": screenshot_path,
                    "platform": self.platform,
                    "account_id": self.account_id
                }
            )
        
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout:
            if await self._check_verification_completed():
                logger.info(f"{self.platform}平台的{verification_type}验证已完成")
                self.verification_status = "completed"
                self.verification_data["status"] = self.verification_status
                self.verification_data["updated_at"] = datetime.now().isoformat()
                self._save_verification_data()
                return True, self.verification_data.get("result", {})
            
            await asyncio.sleep(retry_interval)
        
        logger.warning(f"{self.platform}平台的{verification_type}验证超时")
        self.verification_status = "timeout"
        self.verification_data["status"] = self.verification_status
        self.verification_data["updated_at"] = datetime.now().isoformat()
        self._save_verification_data()
        
        return False, {"error": "verification_timeout"}
    
    async def handle_captcha(self, selector: str, timeout: int = 300) -> bool:
        """处理图形验证码
        
        Args:
            selector: 验证码元素选择器
            timeout: 超时时间（秒）
            
        Returns:
            验证是否成功
        """
        try:
            if not await self.browser_tool.is_visible(selector, timeout=5000):
                logger.warning(f"验证码元素不存在: {selector}")
                return False
            
            element_info = await self.browser_tool.page.evaluate(f"""() => {{
                const element = document.querySelector('{selector}');
                if (!element) return null;
                const rect = element.getBoundingClientRect();
                return {{
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height
                }};
            }}""")
            
            if not element_info:
                logger.warning(f"无法获取验证码元素位置: {selector}")
                return False
            
            success, result = await self.handle_verification(
                verification_type="captcha",
                verification_details={
                    "selector": selector,
                    "element_info": element_info
                },
                timeout=timeout
            )
            
            return success
        except Exception as e:
            logger.error(f"处理验证码时出错: {e}")
            return False
    
    async def handle_email_verification(self, input_selector: str, timeout: int = 300) -> bool:
        """处理邮箱验证码
        
        Args:
            input_selector: 邮箱验证码输入框选择器
            timeout: 超时时间（秒）
            
        Returns:
            验证是否成功
        """
        try:
            if not await self.browser_tool.is_visible(input_selector, timeout=5000):
                logger.warning(f"邮箱验证码输入框不存在: {input_selector}")
                return False
            
            success, result = await self.handle_verification(
                verification_type="email",
                verification_details={
                    "input_selector": input_selector
                },
                timeout=timeout
            )
            
            if success and "code" in result:
                await self.browser_tool.fill(input_selector, result["code"])
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                if "submit_selector" in result:
                    await self.browser_tool.click(result["submit_selector"])
                else:
                    submit_selectors = [
                        "//button[contains(text(), '确认') or contains(text(), '提交') or contains(text(), '验证')]",
                        "//button[contains(@class, 'submit') or contains(@class, 'confirm')]",
                        "//input[@type='submit']"
                    ]
                    
                    for selector in submit_selectors:
                        try:
                            if await self.browser_tool.is_visible(selector, timeout=1000):
                                await self.browser_tool.click(selector)
                                break
                        except Exception:
                            continue
                
                await asyncio.sleep(random.uniform(2.0, 4.0))
                return True
            
            return False
        except Exception as e:
            logger.error(f"处理邮箱验证码时出错: {e}")
            return False
            
    async def handle_sms_verification(self, input_selector: str, timeout: int = 300) -> bool:
        """处理短信验证码
        
        Args:
            input_selector: 短信验证码输入框选择器
            timeout: 超时时间（秒）
            
        Returns:
            验证是否成功
        """
        try:
            if not await self.browser_tool.is_visible(input_selector, timeout=5000):
                logger.warning(f"短信验证码输入框不存在: {input_selector}")
                return False
            
            success, result = await self.handle_verification(
                verification_type="sms",
                verification_details={
                    "input_selector": input_selector
                },
                timeout=timeout
            )
            
            if success and "code" in result:
                await self.browser_tool.fill(input_selector, result["code"])
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                if "submit_selector" in result:
                    await self.browser_tool.click(result["submit_selector"])
                else:
                    submit_selectors = [
                        "//button[contains(text(), '确认') or contains(text(), '提交') or contains(text(), '验证')]",
                        "//button[contains(@class, 'submit') or contains(@class, 'confirm')]",
                        "//input[@type='submit']"
                    ]
                    
                    for selector in submit_selectors:
                        try:
                            if await self.browser_tool.is_visible(selector, timeout=1000):
                                await self.browser_tool.click(selector)
                                break
                        except Exception:
                            continue
                
                await asyncio.sleep(random.uniform(2.0, 4.0))
                return True
            
            return False
        except Exception as e:
            logger.error(f"处理短信验证码时出错: {e}")
            return False
    
    async def _check_verification_completed(self) -> bool:
        """检查验证是否已完成
        
        Returns:
            验证是否已完成
        """
        verification_file = self.debug_dir / f"verification_{self.verification_id}.json"
        
        if not verification_file.exists():
            return False
        
        try:
            with open(verification_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                if data.get("status") == "completed":
                    self.verification_data = data
                    return True
        except Exception as e:
            logger.error(f"检查验证状态时出错: {e}")
        
        return False
    
    def _save_verification_data(self) -> None:
        """保存验证数据"""
        verification_file = self.debug_dir / f"verification_{self.verification_id}.json"
        
        try:
            with open(verification_file, "w", encoding="utf-8") as f:
                json.dump(self.verification_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存验证数据时出错: {e}")
    
    async def _take_verification_screenshot(self, name: str) -> str:
        """截取验证页面截图
        
        Args:
            name: 截图名称
            
        Returns:
            截图路径
        """
        if not self.browser_tool:
            return ""
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        screenshot_filename = f"verification_{self.platform}_{name}_{timestamp}.png"
        
        try:
            screenshot_path = await self.browser_tool.screenshot(
                str(self.debug_dir / screenshot_filename)
            )
            logger.info(f"验证截图已保存到: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.error(f"验证截图失败: {e}")
            return ""
    
    @staticmethod
    async def complete_verification(
        verification_id: str, 
        result: Dict[str, Any],
        verification_dir: Optional[str] = None
    ) -> bool:
        """完成验证
        
        Args:
            verification_id: 验证ID
            result: 验证结果
            verification_dir: 验证数据目录
            
        Returns:
            是否成功完成验证
        """
        verification_dir = Path(verification_dir) if verification_dir else Path("/tmp/promora_verification")
        verification_file = verification_dir / f"verification_{verification_id}.json"
        
        if not verification_file.exists():
            logger.error(f"验证数据文件不存在: {verification_file}")
            return False
        
        try:
            with open(verification_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            data["status"] = "completed"
            data["result"] = result
            data["updated_at"] = datetime.now().isoformat()
            
            with open(verification_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"验证已完成: {verification_id}")
            return True
        except Exception as e:
            logger.error(f"完成验证时出错: {e}")
            return False
