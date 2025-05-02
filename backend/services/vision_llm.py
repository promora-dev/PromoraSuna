"""
Vision LLM API interface for making calls to vision-capable language models.

This module provides functionality for making API calls to vision-capable LLMs
(primarily GPT-4.1) to analyze images and extract information.
"""

import os
import base64
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
import aiohttp
from pathlib import Path

from utils.logger import logger
from utils.config import config

MAX_RETRIES = 3
RETRY_DELAY = 5
RATE_LIMIT_DELAY = 30

class VisionLLMError(Exception):
    """Base exception for Vision LLM-related errors."""
    pass

async def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64-encoded image string
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding image to base64: {str(e)}")
        raise VisionLLMError(f"Failed to encode image: {str(e)}")

async def analyze_image_with_gpt4_vision(
    image_path: str,
    prompt: str,
    api_key: Optional[str] = None,
    max_tokens: int = 500,
    temperature: float = 0.5,
    detail_level: str = "high"
) -> Dict[str, Any]:
    """
    Analyze an image using GPT-4.1 (with vision capabilities).
    
    Args:
        image_path: Path to the image file
        prompt: Text prompt describing what to analyze in the image
        api_key: OpenAI API key (optional, will use config if not provided)
        max_tokens: Maximum tokens in the response
        temperature: Sampling temperature (0-1)
        detail_level: Detail level for image analysis ("low", "high", "auto")
        
    Returns:
        Dict containing the analysis results
        
    Raises:
        VisionLLMError: If API call fails
    """
    api_key = api_key or config.OPENAI_API_KEY
    if not api_key:
        raise VisionLLMError("No OpenAI API key provided")
    
    try:
        base64_image = await encode_image_to_base64(image_path)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "gpt-4.1",  # 使用GPT-4.1 API
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text", 
                            "text": prompt
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    ]
                }
            ]
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.debug(f"Making GPT-4.1 API call (attempt {attempt + 1}/{MAX_RETRIES})")
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.openai.com/v1/responses",
                        headers=headers,
                        json=payload
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.debug(f"Successfully received GPT-4.1 API response: {result}")
                            return result
                        else:
                            error_text = await response.text()
                            logger.warning(f"GPT-4.1 API error (status {response.status}): {error_text}")
                            
                            if response.status == 429:  # Rate limit
                                logger.warning(f"Rate limit hit, waiting {RATE_LIMIT_DELAY} seconds")
                                await asyncio.sleep(RATE_LIMIT_DELAY)
                            else:
                                logger.warning(f"Waiting {RETRY_DELAY} seconds before retry")
                                await asyncio.sleep(RETRY_DELAY)
            except Exception as e:
                logger.error(f"Error during GPT-4.1 API call: {str(e)}")
                await asyncio.sleep(RETRY_DELAY)
        
        raise VisionLLMError(f"Failed to make GPT-4.1 API call after {MAX_RETRIES} attempts")
    except Exception as e:
        logger.error(f"Error in analyze_image_with_gpt4_vision: {str(e)}")
        raise VisionLLMError(f"Image analysis failed: {str(e)}")

async def detect_button_in_image(
    image_path: str,
    button_description: str = "Next button",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Detect a button in an image and provide coordinates for clicking.
    
    Args:
        image_path: Path to the image file
        button_description: Description of the button to detect
        api_key: OpenAI API key (optional, will use config if not provided)
        
    Returns:
        Dict containing button detection results, including:
        - found: Whether the button was found
        - coordinates: (x, y) coordinates for clicking
        - confidence: Confidence level (0-1)
        - description: Text description of the button
        - recommendation: Recommended action
    """
    prompt = f"""
    分析这个截图，找到"{button_description}"按钮的位置。
    
    请提供以下信息：
    1. 按钮是否存在于图像中
    2. 按钮的精确坐标（x, y）用于点击
    3. 按钮上的文本内容
    4. 按钮的状态（是否可点击）
    5. 点击该按钮的最佳方式（直接点击、Tab导航后回车等）
    
    请以JSON格式返回结果，包含以下字段：
    {{
        "found": true/false,
        "coordinates": [x, y],
        "button_text": "按钮上的文本",
        "clickable": true/false,
        "recommendation": "推荐的点击方式"
    }}
    
    只返回JSON格式的结果，不要有其他解释。
    """
    
    try:
        result = await analyze_image_with_gpt4_vision(
            image_path=image_path,
            prompt=prompt,
            api_key=api_key,
            temperature=0.2  # Lower temperature for more deterministic results
        )
        
        if "output" in result and "text" in result["output"]:
            content = result["output"]["text"]
            
            import json
            import re
            
            json_match = re.search(r'({.*})', content, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(1)
                    button_data = json.loads(json_str)
                    logger.debug(f"Successfully parsed button data: {button_data}")
                    return button_data
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from response: {content}")
            
            logger.warning(f"No valid JSON found in response: {content}")
            return {
                "found": False,
                "error": "Failed to parse button data from response",
                "raw_response": content
            }
        else:
            logger.warning("No output.text in GPT-4.1 API response")
            return {
                "found": False,
                "error": "No response from GPT-4.1 API"
            }
    except Exception as e:
        logger.error(f"Error in detect_button_in_image: {str(e)}")
        return {
            "found": False,
            "error": str(e)
        }
