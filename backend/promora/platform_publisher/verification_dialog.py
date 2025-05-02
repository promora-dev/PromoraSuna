"""
验证对话模块

此模块提供了一个交互式对话界面，用于用户输入验证码或完成其他验证挑战。
"""

import os
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger("agentpress")

class VerificationDialog:
    """验证对话类，用于与用户交互获取验证信息"""
    
    def __init__(
        self, 
        platform: str,
        account_id: str,
        verification_dir: Optional[str] = None,
        notification_callback: Optional[callable] = None
    ):
        """初始化验证对话
        
        Args:
            platform: 平台名称
            account_id: 账户ID
            verification_dir: 验证数据保存目录
            notification_callback: 通知回调函数
        """
        self.platform = platform
        self.account_id = account_id
        self.verification_dir = Path(verification_dir) if verification_dir else Path("/tmp/promora_verification")
        self.verification_dir.mkdir(exist_ok=True)
        self.notification_callback = notification_callback
        self.verification_id = f"{platform}_{account_id}_{int(datetime.now().timestamp())}"
        
    async def request_verification(
        self, 
        verification_type: str,
        verification_details: Dict[str, Any],
        screenshot_path: Optional[str] = None,
        timeout: int = 300
    ) -> Tuple[bool, Dict[str, Any]]:
        """请求用户进行验证
        
        Args:
            verification_type: 验证类型
            verification_details: 验证详情
            screenshot_path: 验证截图路径
            timeout: 超时时间（秒）
            
        Returns:
            (成功标志, 验证结果数据)
        """
        verification_data = {
            "id": self.verification_id,
            "platform": self.platform,
            "account_id": self.account_id,
            "type": verification_type,
            "details": verification_details,
            "screenshot": screenshot_path,
            "status": "waiting",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "result": None
        }
        
        verification_file = self.verification_dir / f"verification_{self.verification_id}.json"
        with open(verification_file, "w", encoding="utf-8") as f:
            json.dump(verification_data, f, ensure_ascii=False, indent=2)
        
        message = self._generate_verification_message(verification_type, verification_details, screenshot_path)
        if self.notification_callback:
            await self.notification_callback(message, verification_data)
        else:
            logger.info(f"需要用户验证: {message}")
            print(f"\n需要用户验证: {message}")
            if screenshot_path:
                print(f"验证截图: {screenshot_path}")
        
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout:
            try:
                with open(verification_file, "r", encoding="utf-8") as f:
                    current_data = json.load(f)
                    
                if current_data.get("status") == "completed" and current_data.get("result"):
                    logger.info(f"用户已完成验证: {current_data['result']}")
                    return True, current_data["result"]
                
                if current_data.get("status") == "cancelled":
                    logger.warning("用户取消了验证")
                    return False, {"error": "user_cancelled"}
            except Exception as e:
                logger.error(f"读取验证数据时出错: {e}")
            
            await asyncio.sleep(2)
        
        logger.warning(f"验证超时: {self.verification_id}")
        
        try:
            with open(verification_file, "r", encoding="utf-8") as f:
                current_data = json.load(f)
            
            current_data["status"] = "timeout"
            current_data["updated_at"] = datetime.now().isoformat()
            
            with open(verification_file, "w", encoding="utf-8") as f:
                json.dump(current_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"更新验证状态时出错: {e}")
        
        return False, {"error": "verification_timeout"}
    
    def _generate_verification_message(
        self, 
        verification_type: str,
        verification_details: Dict[str, Any],
        screenshot_path: Optional[str]
    ) -> str:
        """生成验证消息
        
        Args:
            verification_type: 验证类型
            verification_details: 验证详情
            screenshot_path: 验证截图路径
            
        Returns:
            验证消息
        """
        platform_name = {
            "zhihu": "知乎",
            "x": "X (Twitter)",
            "linkedin": "LinkedIn",
            "medium": "Medium"
        }.get(self.platform, self.platform)
        
        if verification_type == "captcha":
            return f"请输入{platform_name}的图形验证码。验证ID: {self.verification_id}"
        elif verification_type == "sms":
            return f"请输入{platform_name}发送的短信验证码。验证ID: {self.verification_id}"
        elif verification_type == "email":
            return f"请输入{platform_name}发送到您邮箱的验证码。验证ID: {self.verification_id}"
        elif verification_type == "security_verification":
            return f"请完成{platform_name}的安全验证。验证ID: {self.verification_id}"
        else:
            return f"请完成{platform_name}的验证。验证类型: {verification_type}。验证ID: {self.verification_id}"
    
    @staticmethod
    async def submit_verification_result(
        verification_id: str,
        result: Dict[str, Any],
        verification_dir: Optional[str] = None
    ) -> bool:
        """提交验证结果
        
        Args:
            verification_id: 验证ID
            result: 验证结果
            verification_dir: 验证数据目录
            
        Returns:
            是否成功提交
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
            
            logger.info(f"验证结果已提交: {verification_id}")
            return True
        except Exception as e:
            logger.error(f"提交验证结果时出错: {e}")
            return False
    
    @staticmethod
    async def cancel_verification(
        verification_id: str,
        reason: str = "user_cancelled",
        verification_dir: Optional[str] = None
    ) -> bool:
        """取消验证
        
        Args:
            verification_id: 验证ID
            reason: 取消原因
            verification_dir: 验证数据目录
            
        Returns:
            是否成功取消
        """
        verification_dir = Path(verification_dir) if verification_dir else Path("/tmp/promora_verification")
        verification_file = verification_dir / f"verification_{verification_id}.json"
        
        if not verification_file.exists():
            logger.error(f"验证数据文件不存在: {verification_file}")
            return False
        
        try:
            with open(verification_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            data["status"] = "cancelled"
            data["result"] = {"error": reason}
            data["updated_at"] = datetime.now().isoformat()
            
            with open(verification_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"验证已取消: {verification_id}")
            return True
        except Exception as e:
            logger.error(f"取消验证时出错: {e}")
            return False
