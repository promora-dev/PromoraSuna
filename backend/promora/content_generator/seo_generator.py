"""
SEO content generation tool for Promora.

This module provides functionality for generating SEO-optimized content
and platform-specific summaries using LLM integration.
"""

import json
from typing import List, Dict, Any, Optional, Union, AsyncGenerator

from services.llm import make_llm_api_call
from services.mock_llm import mock_llm_api_call
from utils.logger import logger
from .models import ContentRequest, GeneratedContent, PlatformSummary


class SEOContentGenerator:
    """Tool for generating SEO-optimized content and platform-specific summaries."""
    
    def __init__(self, llm_model: str = "gpt-4o"):
        """Initialize the SEO content generator.
        
        Args:
            llm_model: LLM model to use for content generation
        """
        self.llm_model = llm_model
    
    async def generate_content(self, request: ContentRequest) -> GeneratedContent:
        """Generate SEO-optimized content based on the request.
        
        Args:
            request: Content generation request
            
        Returns:
            Generated content with platform-specific summaries
        """
        main_content = await self._generate_main_content(request)
        
        platforms = ["X", "LinkedIn", "Medium", "Zhihu"]
        summaries = await self._generate_platform_summaries(main_content, platforms, request.language)
        
        return GeneratedContent(
            title=main_content["title"],
            main_content=main_content["content"],
            meta_description=main_content["meta_description"],
            keywords=request.keywords,
            summaries=summaries,
            language=request.language
        )
        
    async def generate_seo_content(self, keyword: str, industry: str, audience: str, language: str = "en", 
                                  brand_materials: Optional[List[str]] = None, tone: str = "professional", 
                                  length: str = "medium") -> Dict[str, Any]:
        """Generate SEO-optimized content based on the provided parameters.
        
        Args:
            keyword: Primary keyword to target in the content
            industry: Industry or niche for the content
            audience: Target audience for the content
            language: Language for the content
            brand_materials: Optional brand materials or existing content fragments
            tone: Tone of the content
            length: Length of the content
            
        Returns:
            Dictionary containing the generated content details
        """
        import uuid
        from datetime import datetime
        
        request = ContentRequest(
            keywords=[keyword],
            industry=industry,
            audience=audience,
            content_type="article",
            language=language,
            brand_materials=brand_materials,
            tone=tone,
            length=length
        )
        
        # Generate the content
        content = await self.generate_content(request)
        
        result = {
            "content_id": str(uuid.uuid4()),
            "content": content,
            "generated_at": datetime.now().isoformat()
        }
        
        return result
        
    async def generate_platform_summary(self, content: str, platform: Any, language: str = "en", 
                                       max_length: Optional[int] = None) -> PlatformSummary:
        """Generate a platform-specific summary for the content.
        
        Args:
            content: Original content to summarize
            platform: Platform to generate summary for
            language: Language for the summary
            max_length: Maximum length of the summary in characters
            
        Returns:
            Platform-specific summary
        """
        system_prompt = self._get_summary_system_prompt(language)
        
        user_prompt = f"""
        Please create a platform-specific summary for the following content:
        
        Content: {content}
        
        Generate a summary for this platform: {platform}
        
        For the platform, provide:
        1. Platform-specific content summary
        2. Relevant hashtags (if applicable)
        3. A prompt for generating an image for this content
        
        Format your response as a JSON object with 'platform', 'content', 'hashtags', and 'image_prompt' fields.
        """
        
        if max_length:
            user_prompt += f"\n\nThe summary should be no longer than {max_length} characters."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        logger.info(f"Generating platform summary for {platform}")
        try:
            response = await make_llm_api_call(
                messages=messages,
                model_name=self.llm_model,
                temperature=0.7,
                max_tokens=1000
            )
        except Exception as e:
            logger.warning(f"Error making LLM API call: {str(e)}. Using mock LLM service.")
            response = await mock_llm_api_call(
                messages=messages,
                model_name=self.llm_model,
                temperature=0.7
            )
        
        try:
            summary_text = self._extract_content_from_response(response)
            summary_json = json.loads(summary_text)
            
            return PlatformSummary(
                platform=str(platform),
                content=summary_json["content"],
                hashtags=summary_json.get("hashtags"),
                image_prompt=summary_json.get("image_prompt")
            )
        except Exception as e:
            logger.error(f"Error parsing platform summary response: {e}")
            return PlatformSummary(
                platform=str(platform),
                content=f"Summary for {platform}",
                hashtags=["content", "marketing", "ai"],
                image_prompt=f"An image representing content for {platform}"
            )
    
    async def _generate_main_content(self, request: ContentRequest) -> Dict[str, Any]:
        """Generate the main SEO-optimized content.
        
        Args:
            request: Content generation request
            
        Returns:
            Dictionary containing title, content, and meta description
        """
        system_prompt = self._get_seo_system_prompt(request.language)
        
        user_prompt = self._format_content_request(request)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        logger.info(f"Generating SEO content for keywords: {request.keywords}")
        try:
            response = await make_llm_api_call(
                messages=messages,
                model_name=self.llm_model,
                temperature=0.7,
                max_tokens=4000
            )
        except Exception as e:
            logger.warning(f"Error making LLM API call: {str(e)}. Using mock LLM service.")
            response = await mock_llm_api_call(
                messages=messages,
                model_name=self.llm_model,
                temperature=0.7
            )
        
        try:
            content_text = self._extract_content_from_response(response)
            content_json = json.loads(content_text)
            
            return {
                "title": content_json["title"],
                "content": content_json["content"],
                "meta_description": content_json["meta_description"]
            }
        except Exception as e:
            logger.error(f"Error parsing content generation response: {e}")
            return {
                "title": "Generated Content",
                "content": self._extract_content_from_response(response),
                "meta_description": f"Article about {', '.join(request.keywords)}"
            }
    
    async def _generate_platform_summaries(
        self, 
        main_content: Dict[str, Any], 
        platforms: List[str],
        language: str
    ) -> List[PlatformSummary]:
        """Generate platform-specific summaries for the content.
        
        Args:
            main_content: Main content dictionary
            platforms: List of platforms to generate summaries for
            language: Language for the summaries
            
        Returns:
            List of platform-specific summaries
        """
        system_prompt = self._get_summary_system_prompt(language)
        
        user_prompt = f"""
        Please create platform-specific summaries for the following content:
        
        Title: {main_content['title']}
        
        Content: {main_content['content']}
        
        Meta Description: {main_content['meta_description']}
        
        Generate summaries for these platforms: {', '.join(platforms)}
        
        For each platform, provide:
        1. Platform-specific content summary
        2. Relevant hashtags (if applicable)
        3. A prompt for generating an image for this content
        
        Format your response as a JSON array of objects with 'platform', 'content', 'hashtags', and 'image_prompt' fields.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        logger.info(f"Generating platform summaries for {len(platforms)} platforms")
        try:
            response = await make_llm_api_call(
                messages=messages,
                model_name=self.llm_model,
                temperature=0.7,
                max_tokens=2000
            )
        except Exception as e:
            logger.warning(f"Error making LLM API call: {str(e)}. Using mock LLM service.")
            response = await mock_llm_api_call(
                messages=messages,
                model_name=self.llm_model,
                temperature=0.7
            )
        
        try:
            summary_text = self._extract_content_from_response(response)
            summaries_json = json.loads(summary_text)
            
            return [
                PlatformSummary(
                    platform=summary["platform"],
                    content=summary["content"],
                    hashtags=summary.get("hashtags"),
                    image_prompt=summary.get("image_prompt")
                )
                for summary in summaries_json
            ]
        except Exception as e:
            logger.error(f"Error parsing platform summaries response: {e}")
            return [
                PlatformSummary(
                    platform=platform,
                    content=f"Summary of {main_content['title']} for {platform}",
                    hashtags=["content", "marketing", "ai"],
                    image_prompt=f"An image representing {main_content['title']}"
                )
                for platform in platforms
            ]
    
    def _extract_content_from_response(self, response: Union[Dict[str, Any], AsyncGenerator]) -> str:
        """Extract content from LLM response regardless of its type.
        
        Args:
            response: LLM response (either Dict or AsyncGenerator)
            
        Returns:
            Extracted content as string
        """
        if isinstance(response, dict):
            if 'choices' in response and len(response['choices']) > 0:
                if 'message' in response['choices'][0]:
                    return response['choices'][0]['message']['content']
                elif 'text' in response['choices'][0]:
                    return response['choices'][0]['text']
            
            return str(response)
        
        return "Content from streaming response"
    
    def _get_seo_system_prompt(self, language: str) -> str:
        """Get the system prompt for SEO content generation.
        
        Args:
            language: Language for the content
            
        Returns:
            System prompt for SEO content generation
        """
        if language == "zh":
            return """
            你是一位专业的SEO内容创作者，擅长创建针对搜索引擎优化的高质量内容。
            你的任务是根据提供的关键词、行业和受众，创建一篇SEO优化的文章。
            
            请遵循以下SEO最佳实践：
            1. 在标题、开头段落和全文中自然地使用关键词
            2. 创建引人入胜的标题，包含主要关键词
            3. 使用小标题（H2、H3）组织内容，并在其中包含关键词变体
            4. 编写简洁的元描述，包含主要关键词
            5. 确保内容深度、原创且有价值
            6. 使用自然语言，避免关键词堆砌
            7. 包含相关的长尾关键词
            
            以JSON格式返回你的响应，包含以下字段：
            - title: 文章标题
            - content: 完整的文章内容，包括HTML标记
            - meta_description: SEO元描述
            """
        else:
            return """
            You are a professional SEO content creator skilled at creating high-quality content optimized for search engines.
            Your task is to create an SEO-optimized article based on the provided keywords, industry, and audience.
            
            Follow these SEO best practices:
            1. Use keywords naturally in the title, opening paragraph, and throughout the content
            2. Create an engaging title that includes the primary keyword
            3. Use subheadings (H2, H3) to organize content and include keyword variations
            4. Write a concise meta description that includes the primary keyword
            5. Ensure content is deep, original, and valuable
            6. Use natural language and avoid keyword stuffing
            7. Include relevant long-tail keywords
            
            Return your response in JSON format with the following fields:
            - title: The article title
            - content: The full article content with HTML markup
            - meta_description: The SEO meta description
            """
    
    def _get_summary_system_prompt(self, language: str) -> str:
        """Get the system prompt for platform summary generation.
        
        Args:
            language: Language for the summaries
            
        Returns:
            System prompt for platform summary generation
        """
        if language == "zh":
            return """
            你是一位专业的社交媒体内容创作者，擅长为不同平台创建优化的内容摘要。
            你的任务是根据提供的文章，为各个平台创建定制的内容摘要。
            
            请为每个平台遵循以下最佳实践：
            
            X（Twitter）:
            - 简洁有力，280字符以内
            - 使用相关话题标签（2-3个）
            - 包含引人点击的号召性用语
            
            LinkedIn:
            - 专业语调，1-3段
            - 强调行业见解和专业知识
            - 使用相关话题标签（3-5个）
            
            Medium:
            - 引人入胜的开场白，1-2段
            - 包含文章的主要观点
            - 使用相关话题标签（3-5个）
            
            知乎:
            - 提出引人思考的问题
            - 提供专业见解，2-3段
            - 使用适合知乎的格式和语调
            
            以JSON数组格式返回你的响应，每个平台一个对象，包含以下字段：
            - platform: 平台名称
            - content: 平台特定的内容摘要
            - hashtags: 相关话题标签数组
            - image_prompt: 为该内容生成图像的提示
            """
        else:
            return """
            You are a professional social media content creator skilled at creating optimized content summaries for different platforms.
            Your task is to create platform-specific summaries based on the provided article.
            
            Follow these best practices for each platform:
            
            X (Twitter):
            - Concise and impactful, under 280 characters
            - Use relevant hashtags (2-3)
            - Include a compelling call-to-action
            
            LinkedIn:
            - Professional tone, 1-3 paragraphs
            - Emphasize industry insights and expertise
            - Use relevant hashtags (3-5)
            
            Medium:
            - Engaging opening, 1-2 paragraphs
            - Include the main points of the article
            - Use relevant tags (3-5)
            
            Zhihu:
            - Pose a thought-provoking question
            - Provide expert insights, 2-3 paragraphs
            - Use format and tone appropriate for Zhihu
            
            Return your response as a JSON array of objects, one for each platform, with the following fields:
            - platform: The platform name
            - content: The platform-specific content summary
            - hashtags: An array of relevant hashtags
            - image_prompt: A prompt for generating an image for this content
            """
    
    def _format_content_request(self, request: ContentRequest) -> str:
        """Format the content request as a user prompt.
        
        Args:
            request: Content generation request
            
        Returns:
            Formatted user prompt
        """
        brand_materials = ""
        if request.brand_materials:
            brand_materials = f"\nBrand Materials:\n{json.dumps(request.brand_materials, ensure_ascii=False)}"
        
        if request.language == "zh":
            return f"""
            请为以下要求创建SEO优化内容：
            
            关键词：{json.dumps(request.keywords, ensure_ascii=False)}
            行业：{request.industry}
            目标受众：{request.audience}
            内容类型：{request.content_type}
            语调：{request.tone}
            长度：{request.length}{brand_materials}
            
            请创建一篇完整的SEO优化文章，包括标题、内容和元描述。以JSON格式返回。
            """
        else:
            return f"""
            Please create SEO-optimized content for the following requirements:
            
            Keywords: {json.dumps(request.keywords, ensure_ascii=False)}
            Industry: {request.industry}
            Target Audience: {request.audience}
            Content Type: {request.content_type}
            Tone: {request.tone}
            Length: {request.length}{brand_materials}
            
            Please create a complete SEO-optimized article including title, content, and meta description. Return in JSON format.
            """
