"""
Mock Vision LLM API interface for testing without real API keys.

This module provides mock implementations of vision LLM API calls for testing purposes.
It returns predefined responses for different types of image analysis requests.
"""

import json
import uuid
import os
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from utils.logger import logger


class MockVisionLLMError(Exception):
    """Base exception for Mock Vision LLM-related errors."""
    pass


async def mock_analyze_image_with_gpt4_vision(
    image_path: str,
    prompt: str,
    api_key: Optional[str] = None,
    max_tokens: int = 500,
    temperature: float = 0.5,
    detail_level: str = "high"
) -> Dict[str, Any]:
    """
    Mock implementation of analyze_image_with_gpt4_vision that returns predefined responses.
    
    Args:
        image_path: Path to the image file
        prompt: Text prompt describing what to analyze in the image
        api_key: OpenAI API key (optional, will use config if not provided)
        max_tokens: Maximum tokens in the response
        temperature: Sampling temperature (0-1)
        detail_level: Detail level for image analysis ("low", "high", "auto")
        
    Returns:
        Dict containing the mock analysis results
    """
    logger.info(f"Using mock vision LLM API call for image: {image_path}")
    
    filename = os.path.basename(image_path)
    
    if "按钮" in prompt or "button" in prompt:
        return mock_button_detection_response(filename)
    elif "分析这个页面" in prompt or "analyze this page" in prompt:
        return mock_page_analysis_response(filename)
    else:
        return mock_general_image_analysis_response(filename)


def mock_button_detection_response(filename: str) -> Dict[str, Any]:
    """Generate a mock button detection response based on the image filename."""
    default_response = {
        "output": {
            "text": json.dumps({
                "found": True,
                "coordinates": [640, 450],
                "button_text": "Next",
                "clickable": True,
                "recommendation": "直接点击按钮中心位置"
            })
        }
    }
    
    if "analyze_1_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "found": True,
                    "coordinates": [640, 380],
                    "button_text": "Create account",
                    "clickable": True,
                    "recommendation": "直接点击'Create account'按钮"
                })
            }
        }
    elif "analyze_2_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "found": True,
                    "coordinates": [640, 450],
                    "button_text": "Next",
                    "clickable": True,
                    "recommendation": "填写姓名后点击'Next'按钮"
                })
            }
        }
    elif "analyze_3_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "found": True,
                    "coordinates": [640, 450],
                    "button_text": "Next",
                    "clickable": True,
                    "recommendation": "填写邮箱后点击'Next'按钮"
                })
            }
        }
    elif "analyze_4_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "found": True,
                    "coordinates": [640, 500],
                    "button_text": "Next",
                    "clickable": True,
                    "recommendation": "选择生日后点击'Next'按钮"
                })
            }
        }
    elif "analyze_5_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "found": True,
                    "coordinates": [640, 550],
                    "button_text": "Next",
                    "clickable": True,
                    "recommendation": "点击'Next'按钮继续"
                })
            }
        }
    elif "analyze_6_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "found": True,
                    "coordinates": [640, 450],
                    "button_text": "Next",
                    "clickable": True,
                    "recommendation": "点击'Next'按钮继续"
                })
            }
        }
    elif "analyze_7_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "found": True,
                    "coordinates": [640, 450],
                    "button_text": "Next",
                    "clickable": True,
                    "recommendation": "点击'Next'按钮继续"
                })
            }
        }
    elif "analyze_8_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "found": True,
                    "coordinates": [640, 450],
                    "button_text": "Next",
                    "clickable": True,
                    "recommendation": "点击'Next'按钮继续"
                })
            }
        }
    elif "analyze_9_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "found": True,
                    "coordinates": [640, 450],
                    "button_text": "Next",
                    "clickable": True,
                    "recommendation": "点击'Next'按钮继续"
                })
            }
        }
    elif "analyze_10_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "found": True,
                    "coordinates": [640, 450],
                    "button_text": "Next",
                    "clickable": True,
                    "recommendation": "点击'Next'按钮继续"
                })
            }
        }
    elif "analyze_11_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "found": True,
                    "coordinates": [640, 450],
                    "button_text": "Next",
                    "clickable": True,
                    "recommendation": "点击'Next'按钮继续"
                })
            }
        }
    elif "analyze_12_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "found": True,
                    "coordinates": [640, 450],
                    "button_text": "Next",
                    "clickable": True,
                    "recommendation": "点击'Next'按钮继续"
                })
            }
        }
    elif "analyze_13_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "found": True,
                    "coordinates": [640, 450],
                    "button_text": "Next",
                    "clickable": True,
                    "recommendation": "点击'Next'按钮继续"
                })
            }
        }
    elif "analyze_14_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "found": True,
                    "coordinates": [640, 450],
                    "button_text": "Next",
                    "clickable": True,
                    "recommendation": "点击'Next'按钮继续"
                })
            }
        }
    elif "analyze_15_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "found": True,
                    "coordinates": [640, 450],
                    "button_text": "完成注册",
                    "clickable": True,
                    "recommendation": "点击'完成注册'按钮完成注册流程"
                })
            }
        }
    elif "analyze_16_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "found": True,
                    "coordinates": [640, 450],
                    "button_text": "开始使用",
                    "clickable": True,
                    "recommendation": "点击'开始使用'按钮完成注册并开始使用X"
                })
            }
        }
    
    return default_response


def mock_page_analysis_response(filename: str) -> Dict[str, Any]:
    """Generate a mock page analysis response based on the image filename."""
    default_response = {
        "output": {
            "text": json.dumps({
                "page_type": "X注册流程",
                "registration_step": "未知步骤",
                "elements": [
                    {
                        "type": "按钮",
                        "description": "下一步按钮",
                        "coordinates": [640, 450],
                        "is_active": True
                    }
                ],
                "suggested_actions": [
                    {
                        "type": "click",
                        "target": "下一步按钮",
                        "coordinates": [640, 450]
                    }
                ],
                "next_step": "继续注册流程"
            })
        }
    }
    
    if "analyze_1_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "page_type": "X注册流程 - 初始页面",
                    "registration_step": "开始注册",
                    "elements": [
                        {
                            "type": "按钮",
                            "description": "创建账号按钮",
                            "coordinates": [640, 380],
                            "is_active": True
                        }
                    ],
                    "suggested_actions": [
                        {
                            "type": "click",
                            "target": "创建账号按钮",
                            "coordinates": [640, 380]
                        }
                    ],
                    "next_step": "输入个人信息"
                })
            }
        }
    elif "analyze_2_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "page_type": "X注册流程 - 个人信息页面",
                    "registration_step": "输入姓名",
                    "elements": [
                        {
                            "type": "输入框",
                            "description": "姓名输入框",
                            "coordinates": [640, 300],
                            "is_active": True
                        },
                        {
                            "type": "按钮",
                            "description": "下一步按钮",
                            "coordinates": [640, 450],
                            "is_active": True
                        }
                    ],
                    "suggested_actions": [
                        {
                            "type": "type",
                            "target": "姓名输入框",
                            "coordinates": [640, 300],
                            "value": "Promora AI"
                        },
                        {
                            "type": "click",
                            "target": "下一步按钮",
                            "coordinates": [640, 450]
                        }
                    ],
                    "next_step": "输入邮箱"
                })
            }
        }
    elif "analyze_3_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "page_type": "X注册流程 - 邮箱输入页面",
                    "registration_step": "输入邮箱",
                    "elements": [
                        {
                            "type": "输入框",
                            "description": "邮箱输入框",
                            "coordinates": [640, 300],
                            "is_active": True
                        },
                        {
                            "type": "按钮",
                            "description": "下一步按钮",
                            "coordinates": [640, 450],
                            "is_active": True
                        }
                    ],
                    "suggested_actions": [
                        {
                            "type": "type",
                            "target": "邮箱输入框",
                            "coordinates": [640, 300],
                            "value": "test@example.com"
                        },
                        {
                            "type": "click",
                            "target": "下一步按钮",
                            "coordinates": [640, 450]
                        }
                    ],
                    "next_step": "选择生日"
                })
            }
        }
    elif "analyze_4_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "page_type": "X注册流程 - 生日选择页面",
                    "registration_step": "选择生日",
                    "elements": [
                        {
                            "type": "下拉框",
                            "description": "月份选择",
                            "coordinates": [540, 300],
                            "is_active": True
                        },
                        {
                            "type": "下拉框",
                            "description": "日期选择",
                            "coordinates": [640, 300],
                            "is_active": True
                        },
                        {
                            "type": "下拉框",
                            "description": "年份选择",
                            "coordinates": [740, 300],
                            "is_active": True
                        },
                        {
                            "type": "按钮",
                            "description": "下一步按钮",
                            "coordinates": [640, 500],
                            "is_active": True
                        }
                    ],
                    "suggested_actions": [
                        {
                            "type": "select",
                            "target": "月份选择",
                            "coordinates": [540, 300],
                            "value": "7"
                        },
                        {
                            "type": "select",
                            "target": "日期选择",
                            "coordinates": [640, 300],
                            "value": "15"
                        },
                        {
                            "type": "select",
                            "target": "年份选择",
                            "coordinates": [740, 300],
                            "value": "1990"
                        },
                        {
                            "type": "click",
                            "target": "下一步按钮",
                            "coordinates": [640, 500]
                        }
                    ],
                    "next_step": "自定义体验"
                })
            }
        }
    elif "analyze_5_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "page_type": "X注册流程 - 自定义体验页面",
                    "registration_step": "自定义体验",
                    "elements": [
                        {
                            "type": "按钮",
                            "description": "下一步按钮",
                            "coordinates": [640, 550],
                            "is_active": True
                        }
                    ],
                    "suggested_actions": [
                        {
                            "type": "click",
                            "target": "下一步按钮",
                            "coordinates": [640, 550]
                        }
                    ],
                    "next_step": "设置用户名"
                })
            }
        }
    elif "analyze_6_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "page_type": "X注册流程 - 用户名设置页面",
                    "registration_step": "设置用户名",
                    "elements": [
                        {
                            "type": "输入框",
                            "description": "用户名输入框",
                            "coordinates": [640, 300],
                            "is_active": True
                        },
                        {
                            "type": "按钮",
                            "description": "下一步按钮",
                            "coordinates": [640, 450],
                            "is_active": True
                        }
                    ],
                    "suggested_actions": [
                        {
                            "type": "type",
                            "target": "用户名输入框",
                            "coordinates": [640, 300],
                            "value": "PromoraAI"
                        },
                        {
                            "type": "click",
                            "target": "下一步按钮",
                            "coordinates": [640, 450]
                        }
                    ],
                    "next_step": "设置密码"
                })
            }
        }
    elif "analyze_7_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "page_type": "X注册流程 - 密码设置页面",
                    "registration_step": "设置密码",
                    "elements": [
                        {
                            "type": "输入框",
                            "description": "密码输入框",
                            "coordinates": [640, 300],
                            "is_active": True
                        },
                        {
                            "type": "按钮",
                            "description": "下一步按钮",
                            "coordinates": [640, 450],
                            "is_active": True
                        }
                    ],
                    "suggested_actions": [
                        {
                            "type": "type",
                            "target": "密码输入框",
                            "coordinates": [640, 300],
                            "value": "SecurePassword123!"
                        },
                        {
                            "type": "click",
                            "target": "下一步按钮",
                            "coordinates": [640, 450]
                        }
                    ],
                    "next_step": "手机验证"
                })
            }
        }
    elif "analyze_8_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "page_type": "X注册流程 - 手机验证页面",
                    "registration_step": "手机验证",
                    "elements": [
                        {
                            "type": "输入框",
                            "description": "手机号输入框",
                            "coordinates": [640, 300],
                            "is_active": True
                        },
                        {
                            "type": "按钮",
                            "description": "下一步按钮",
                            "coordinates": [640, 450],
                            "is_active": True
                        }
                    ],
                    "suggested_actions": [
                        {
                            "type": "type",
                            "target": "手机号输入框",
                            "coordinates": [640, 300],
                            "value": "13800138000"
                        },
                        {
                            "type": "click",
                            "target": "下一步按钮",
                            "coordinates": [640, 450]
                        }
                    ],
                    "next_step": "验证码确认"
                })
            }
        }
    elif "analyze_9_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "page_type": "X注册流程 - 验证码确认页面",
                    "registration_step": "验证码确认",
                    "elements": [
                        {
                            "type": "输入框",
                            "description": "验证码输入框",
                            "coordinates": [640, 300],
                            "is_active": True
                        },
                        {
                            "type": "按钮",
                            "description": "下一步按钮",
                            "coordinates": [640, 450],
                            "is_active": True
                        }
                    ],
                    "suggested_actions": [
                        {
                            "type": "type",
                            "target": "验证码输入框",
                            "coordinates": [640, 300],
                            "value": "123456"
                        },
                        {
                            "type": "click",
                            "target": "下一步按钮",
                            "coordinates": [640, 450]
                        }
                    ],
                    "next_step": "个人资料设置"
                })
            }
        }
    elif "analyze_10_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "page_type": "X注册流程 - 个人资料设置页面",
                    "registration_step": "个人资料设置",
                    "elements": [
                        {
                            "type": "输入框",
                            "description": "个人简介输入框",
                            "coordinates": [640, 300],
                            "is_active": True
                        },
                        {
                            "type": "按钮",
                            "description": "下一步按钮",
                            "coordinates": [640, 450],
                            "is_active": True
                        }
                    ],
                    "suggested_actions": [
                        {
                            "type": "type",
                            "target": "个人简介输入框",
                            "coordinates": [640, 300],
                            "value": "AI驱动的虚拟首席市场官，为企业提供全自动内容营销和SEO增长解决方案。"
                        },
                        {
                            "type": "click",
                            "target": "下一步按钮",
                            "coordinates": [640, 450]
                        }
                    ],
                    "next_step": "兴趣选择"
                })
            }
        }
    elif "analyze_11_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "page_type": "X注册流程 - 兴趣选择页面",
                    "registration_step": "兴趣选择",
                    "elements": [
                        {
                            "type": "复选框",
                            "description": "兴趣选择框",
                            "coordinates": [640, 300],
                            "is_active": True
                        },
                        {
                            "type": "按钮",
                            "description": "下一步按钮",
                            "coordinates": [640, 450],
                            "is_active": True
                        }
                    ],
                    "suggested_actions": [
                        {
                            "type": "click",
                            "target": "兴趣选择框",
                            "coordinates": [640, 300]
                        },
                        {
                            "type": "click",
                            "target": "下一步按钮",
                            "coordinates": [640, 450]
                        }
                    ],
                    "next_step": "头像设置"
                })
            }
        }
    elif "analyze_12_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "page_type": "X注册流程 - 头像设置页面",
                    "registration_step": "头像设置",
                    "elements": [
                        {
                            "type": "按钮",
                            "description": "上传头像按钮",
                            "coordinates": [640, 300],
                            "is_active": True
                        },
                        {
                            "type": "按钮",
                            "description": "跳过按钮",
                            "coordinates": [640, 450],
                            "is_active": True
                        }
                    ],
                    "suggested_actions": [
                        {
                            "type": "click",
                            "target": "跳过按钮",
                            "coordinates": [640, 450]
                        }
                    ],
                    "next_step": "关注推荐"
                })
            }
        }
    elif "analyze_13_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "page_type": "X注册流程 - 关注推荐页面",
                    "registration_step": "关注推荐",
                    "elements": [
                        {
                            "type": "按钮",
                            "description": "跳过按钮",
                            "coordinates": [640, 450],
                            "is_active": True
                        }
                    ],
                    "suggested_actions": [
                        {
                            "type": "click",
                            "target": "跳过按钮",
                            "coordinates": [640, 450]
                        }
                    ],
                    "next_step": "通知设置"
                })
            }
        }
    elif "analyze_14_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "page_type": "X注册流程 - 通知设置页面",
                    "registration_step": "通知设置",
                    "elements": [
                        {
                            "type": "按钮",
                            "description": "跳过按钮",
                            "coordinates": [640, 450],
                            "is_active": True
                        }
                    ],
                    "suggested_actions": [
                        {
                            "type": "click",
                            "target": "跳过按钮",
                            "coordinates": [640, 450]
                        }
                    ],
                    "next_step": "完成注册"
                })
            }
        }
    elif "analyze_15_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "page_type": "X注册流程 - 完成注册页面",
                    "registration_step": "完成注册",
                    "elements": [
                        {
                            "type": "按钮",
                            "description": "完成注册按钮",
                            "coordinates": [640, 450],
                            "is_active": True
                        }
                    ],
                    "suggested_actions": [
                        {
                            "type": "click",
                            "target": "完成注册按钮",
                            "coordinates": [640, 450]
                        }
                    ],
                    "next_step": "开始使用X"
                })
            }
        }
    elif "analyze_16_" in filename:
        return {
            "output": {
                "text": json.dumps({
                    "page_type": "X注册流程 - 注册成功页面",
                    "registration_step": "注册成功",
                    "elements": [
                        {
                            "type": "按钮",
                            "description": "开始使用按钮",
                            "coordinates": [640, 450],
                            "is_active": True
                        }
                    ],
                    "suggested_actions": [
                        {
                            "type": "click",
                            "target": "开始使用按钮",
                            "coordinates": [640, 450]
                        }
                    ],
                    "next_step": "完成"
                })
            }
        }
    
    return default_response


def mock_general_image_analysis_response(filename: str) -> Dict[str, Any]:
    """Generate a mock general image analysis response."""
    return {
        "output": {
            "text": "这是一个X（Twitter）注册页面的截图。页面显示了注册流程中的一个步骤，包含输入框和按钮元素。用户需要填写相关信息并点击下一步按钮继续注册流程。"
        }
    }


async def mock_detect_button_in_image(
    image_path: str,
    button_description: str = "Next button",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mock implementation of detect_button_in_image that returns predefined responses.
    
    Args:
        image_path: Path to the image file
        button_description: Description of the button to detect
        api_key: OpenAI API key (optional, will use config if not provided)
        
    Returns:
        Dict containing mock button detection results
    """
    logger.info(f"Using mock button detection for image: {image_path}")
    
    filename = os.path.basename(image_path)
    
    result = await mock_analyze_image_with_gpt4_vision(
        image_path=image_path,
        prompt=f"分析这个截图，找到\"{button_description}\"按钮的位置。",
        api_key=api_key
    )
    
    if "output" in result and "text" in result["output"]:
        content = result["output"]["text"]
        
        try:
            button_data = json.loads(content)
            logger.debug(f"Successfully parsed mock button data: {button_data}")
            return button_data
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from mock response: {content}")
    
    return {
        "found": True,
        "coordinates": [640, 450],
        "button_text": "Next",
        "clickable": True,
        "recommendation": "直接点击按钮中心位置"
    }
