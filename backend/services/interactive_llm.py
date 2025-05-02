"""
交互式LLM引导系统

该模块提供了使用LLM分析截图并提供交互式引导的功能，
帮助用户完成复杂的网页操作流程，如账户注册、内容发布等。
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path

from utils.logger import logger
from services.vision_llm import analyze_image_with_gpt4_vision

class InteractiveLLMGuidance:
    """交互式LLM引导系统"""
    
    def __init__(self, api_key: Optional[str] = None, debug_dir: Optional[str] = None):
        """初始化交互式LLM引导系统
        
        Args:
            api_key: OpenAI API密钥（可选，如果不提供则使用环境变量）
            debug_dir: 调试信息保存目录（可选）
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("未提供OpenAI API密钥，将无法使用LLM引导功能")
            
        self.debug_dir = debug_dir or "/tmp/promora_llm_guidance"
        os.makedirs(self.debug_dir, exist_ok=True)
        
    async def analyze_page(self, 
                          screenshot_path: str, 
                          context: Dict[str, Any] = None,
                          task_description: str = None) -> Dict[str, Any]:
        """分析页面截图并提供引导
        
        Args:
            screenshot_path: 截图路径
            context: 上下文信息，如当前任务、已完成步骤等
            task_description: 任务描述，如"注册X账户"
            
        Returns:
            包含分析结果的字典，根据平台不同返回不同的结构：
            
            X注册流程返回：
            - step: 当前操作步骤名称
            - fields: 输入字段列表
            - buttons: 可点击按钮列表
            - captcha: 是否存在验证码
            - suggested_action: 建议的下一步操作
            
            其他平台返回：
            - page_type: 页面类型
            - elements: 页面元素列表
            - suggested_actions: 建议的操作列表
            - next_step: 下一步操作
        """
        if not self.api_key:
            logger.error("未提供OpenAI API密钥，无法分析页面")
            return {
                "success": False,
                "error": "未提供OpenAI API密钥"
            }
            
        context = context or {}
        task = task_description or context.get("task", "完成网页操作")
        platform = context.get("platform", "未知平台")
        step = context.get("step", 0)
        
        prompt = self._build_page_analysis_prompt(task, platform, step, context)
        
        try:
            result = await analyze_image_with_gpt4_vision(
                image_path=screenshot_path,
                prompt=prompt,
                api_key=self.api_key
            )
            
            if "output" in result and isinstance(result["output"], list) and len(result["output"]) > 0:
                output_item = result["output"][0]
                if "content" in output_item and isinstance(output_item["content"], list) and len(output_item["content"]) > 0:
                    content_item = output_item["content"][0]
                    if "text" in content_item:
                        content = content_item["text"]
                
                debug_path = os.path.join(self.debug_dir, f"page_analysis_{platform}_{step}_{os.path.basename(screenshot_path)}.json")
                with open(debug_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "prompt": prompt,
                        "response": content,
                        "context": context
                    }, f, ensure_ascii=False, indent=2)
                
                try:
                    import re
                    json_match = re.search(r'```json\s*([\s\S]*?)\s*```|({[\s\S]*})', content)
                    if json_match:
                        json_str = json_match.group(1) or json_match.group(2)
                        
                        json_str = re.sub(r'\[x,\s*y\]', '[100, 100]', json_str)
                        
                        try:
                            analysis_result = json.loads(json_str)
                            analysis_result["success"] = True
                            
                            if platform.lower() == "x" and "注册" in task and "step" in analysis_result:
                                analysis_result["original_format"] = True
                                
                                suggested_actions = []
                                
                                if "fields" in analysis_result:
                                    for field in analysis_result["fields"]:
                                        if "position" in field and "label" in field:
                                            if isinstance(field["position"], list) and len(field["position"]) == 2:
                                                field_key = field["label"].lower()
                                                field_value = ""
                                                
                                                if field_key == "name" or field_key == "display name":
                                                    field_value = context.get("display_name", "Promora AI")
                                                elif field_key == "email" or field_key == "phone or email":
                                                    field_value = context.get("email", "")
                                                elif field_key == "password":
                                                    field_value = context.get("password", "")
                                                elif field_key == "username":
                                                    field_value = context.get("username", "PromoraAI")
                                                
                                                suggested_actions.append({
                                                    "type": "type",
                                                    "target": field["label"],
                                                    "coordinates": field["position"],
                                                    "value": field_value
                                                })
                                
                                if "buttons" in analysis_result:
                                    for button in analysis_result["buttons"]:
                                        if "position" in button and "label" in button:
                                            if isinstance(button["position"], list) and len(button["position"]) == 2:
                                                suggested_actions.append({
                                                    "type": "click",
                                                    "target": button["label"],
                                                    "coordinates": button["position"]
                                                })
                                
                                analysis_result["page_type"] = analysis_result.get("step", "未知步骤")
                                analysis_result["suggested_actions"] = suggested_actions
                                analysis_result["next_step"] = analysis_result.get("suggested_action", "")
                            
                            return analysis_result
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON解析错误: {e}")
                            logger.warning(f"JSON字符串: {json_str}")
                except Exception as e:
                    logger.warning(f"无法解析LLM响应为JSON: {e}")
                    logger.warning(f"原始响应: {content}")
                    
                return {
                    "success": True,
                    "raw_response": content,
                    "page_type": "unknown",
                    "suggested_actions": [{
                        "type": "manual",
                        "description": "LLM未返回结构化数据，请查看原始响应"
                    }]
                }
            else:
                logger.warning("LLM响应中没有内容")
                return {
                    "success": False,
                    "error": "LLM响应中没有内容"
                }
        except Exception as e:
            logger.error(f"分析页面时出错: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_element(self, 
                             screenshot_path: str, 
                             element_description: str,
                             context: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析页面中的特定元素
        
        Args:
            screenshot_path: 截图路径
            element_description: 元素描述，如"下一步按钮"
            context: 上下文信息
            
        Returns:
            包含元素分析结果的字典
        """
        if not self.api_key:
            logger.error("未提供OpenAI API密钥，无法分析元素")
            return {
                "success": False,
                "error": "未提供OpenAI API密钥"
            }
            
        context = context or {}
        platform = context.get("platform", "未知平台")
        
        prompt = self._build_element_analysis_prompt(element_description, platform, context)
        
        try:
            result = await analyze_image_with_gpt4_vision(
                image_path=screenshot_path,
                prompt=prompt,
                api_key=self.api_key
            )
            
            if "output" in result and isinstance(result["output"], list) and len(result["output"]) > 0:
                output_item = result["output"][0]
                if "content" in output_item and isinstance(output_item["content"], list) and len(output_item["content"]) > 0:
                    content_item = output_item["content"][0]
                    if "text" in content_item:
                        content = content_item["text"]
                
                debug_path = os.path.join(self.debug_dir, f"element_analysis_{platform}_{element_description.replace(' ', '_')}_{os.path.basename(screenshot_path)}.json")
                with open(debug_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "prompt": prompt,
                        "response": content,
                        "context": context
                    }, f, ensure_ascii=False, indent=2)
                
                try:
                    import re
                    json_match = re.search(r'```json\s*([\s\S]*?)\s*```|({[\s\S]*})', content)
                    if json_match:
                        json_str = json_match.group(1) or json_match.group(2)
                        
                        json_str = re.sub(r'\[x,\s*y\]', '[100, 100]', json_str)
                        
                        try:
                            analysis_result = json.loads(json_str)
                            analysis_result["success"] = True
                            return analysis_result
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON解析错误: {e}")
                            logger.warning(f"JSON字符串: {json_str}")
                except Exception as e:
                    logger.warning(f"无法解析LLM响应为JSON: {e}")
                    
                return {
                    "success": True,
                    "raw_response": content,
                    "found": False,
                    "reason": "LLM未返回结构化数据"
                }
            else:
                logger.warning("LLM响应中没有内容")
                return {
                    "success": False,
                    "error": "LLM响应中没有内容"
                }
        except Exception as e:
            logger.error(f"分析元素时出错: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_page_analysis_prompt(self, task: str, platform: str, step: int, context: Dict[str, Any]) -> str:
        """构建页面分析提示词
        
        Args:
            task: 任务描述
            platform: 平台名称
            step: 当前步骤
            context: 上下文信息
            
        Returns:
            提示词
        """
        if platform.lower() == "x" and "注册" in task:
            return self._build_x_registration_prompt(step, context)
        elif platform.lower() == "zhihu" and "注册" in task:
            return self._build_zhihu_registration_prompt(step, context)
        else:
            return f"""
            分析这个网页截图，我正在尝试{task}。
            
            请提供以下信息：
            1. 这是什么类型的页面？
            2. 页面上有哪些关键元素（按钮、输入框、链接等）？
            3. 我应该执行什么操作来继续{task}？
            4. 每个操作的具体坐标位置在哪里？
            
            请以JSON格式返回结果，包含以下字段：
            {{
                "page_type": "页面类型描述",
                "elements": [
                    {{
                        "type": "按钮/输入框/链接等",
                        "description": "元素描述",
                        "coordinates": [x, y],
                        "is_active": true/false
                    }}
                ],
                "suggested_actions": [
                    {{
                        "type": "click/type/select等",
                        "target": "操作目标描述",
                        "coordinates": [x, y],
                        "value": "如果是输入操作，要输入的值"
                    }}
                ],
                "next_step": "完成当前页面后的下一步操作"
            }}
            
            只返回JSON格式的结果，不要有其他解释。
            """
    
    def _build_x_registration_prompt(self, step: int, context: Dict[str, Any]) -> str:
        """构建X注册提示词
        
        Args:
            step: 当前步骤
            context: 上下文信息
            
        Returns:
            提示词
        """
        username = context.get("username", "PromoraAI")
        email = context.get("email", "")
        
        return f"""
        你是一位负责截图识别与自动化注册操作的AI助手。我将提供截图（包含注册X账户的界面），请你根据截图内容提取以下信息：

        1. 当前页面的操作步骤名称（如"填写基本信息"）
        2. 页面上的输入字段及其类型（如：Name - 文本输入框；Birth Date - 下拉框）
        3. 页面上可点击按钮的文字及其作用
        4. 是否存在验证码验证或身份验证提示
        5. 建议下一步应该进行的动作（如"点击下一步"、"输入验证码"等）

        我正在尝试注册一个新的X账户，用户名为"{username}"。
        当前是注册流程的第{step}步。

        请使用JSON结构返回，方便自动化处理：
        {{
          "step": "填写基本信息",
          "fields": [
            {{"label": "Name", "type": "text", "position": [320, 250]}},
            {{"label": "Phone or Email", "type": "text", "position": [320, 320]}},
            {{"label": "Date of Birth", "type": "date-selector", "position": [320, 390]}}
          ],
          "buttons": [
            {{"label": "Next", "action": "proceed_to_next_step", "position": [320, 450]}}
          ],
          "captcha": false,
          "suggested_action": "填写以上字段后点击Next"
        }}
        
        注意：
        1. 所有坐标必须是实际的数字，不要使用[x, y]这样的占位符
        2. 坐标值应该是页面上元素的中心位置
        3. 只返回JSON格式的结果，不要有其他解释
        """
    
    def _build_zhihu_registration_prompt(self, step: int, context: Dict[str, Any]) -> str:
        """构建知乎注册提示词
        
        Args:
            step: 当前步骤
            context: 上下文信息
            
        Returns:
            提示词
        """
        username = context.get("username", "")
        email = context.get("email", "")
        
        return f"""
        你是一位负责截图识别与自动化注册操作的AI助手。我将提供截图（包含注册知乎账户的界面），请你根据截图内容提取以下信息：

        1. 当前页面的操作步骤名称（如"填写基本信息"）
        2. 页面上的输入字段及其类型（如：邮箱 - 文本输入框；验证码 - 输入框）
        3. 页面上可点击按钮的文字及其作用
        4. 是否存在验证码验证或身份验证提示
        5. 建议下一步应该进行的动作（如"点击下一步"、"输入验证码"等）

        我正在尝试注册一个新的知乎账户，邮箱为"{email}"。
        当前是注册流程的第{step}步。
        
        请使用JSON结构返回，方便自动化处理：
        {{
          "step": "填写基本信息",
          "fields": [
            {{"label": "邮箱", "type": "text", "position": [320, 250]}},
            {{"label": "密码", "type": "password", "position": [320, 320]}},
            {{"label": "验证码", "type": "text", "position": [320, 390]}}
          ],
          "buttons": [
            {{"label": "注册", "action": "submit_registration", "position": [320, 450]}}
          ],
          "captcha": true,
          "suggested_action": "填写以上字段后点击注册按钮"
        }}
        
        注意：
        1. 所有坐标必须是实际的数字，不要使用[x, y]这样的占位符
        2. 坐标值应该是页面上元素的中心位置
        3. 只返回JSON格式的结果，不要有其他解释
        """
    
    def _build_element_analysis_prompt(self, element_description: str, platform: str, context: Dict[str, Any]) -> str:
        """构建元素分析提示词
        
        Args:
            element_description: 元素描述
            platform: 平台名称
            context: 上下文信息
            
        Returns:
            提示词
        """
        return f"""
        分析这个{platform}页面的截图，找到"{element_description}"的位置。
        
        请提供以下信息：
        1. 元素是否存在于图像中
        2. 元素的精确坐标（x, y）用于点击
        3. 元素的文本内容（如果有）
        4. 元素的状态（是否可点击）
        5. 与元素交互的最佳方式（直接点击、Tab导航后回车等）
        
        请以JSON格式返回结果，包含以下字段：
        {{
            "found": true/false,
            "coordinates": [320, 450],
            "text": "元素上的文本",
            "clickable": true/false,
            "recommendation": "推荐的交互方式"
        }}
        
        注意：
        1. 所有坐标必须是实际的数字，不要使用[x, y]这样的占位符
        2. 坐标值应该是页面上元素的中心位置
        3. 只返回JSON格式的结果，不要有其他解释
        """
