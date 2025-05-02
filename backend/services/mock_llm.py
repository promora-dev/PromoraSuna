"""
Mock LLM API interface for testing without real API keys.

This module provides mock implementations of LLM API calls for testing purposes.
It returns predefined responses for different types of requests.
"""

import json
import uuid
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
import asyncio
from datetime import datetime

from utils.logger import logger


async def mock_llm_api_call(
    messages: List[Dict[str, Any]],
    model_name: str = "mock-gpt-4",
    response_format: Optional[Any] = None,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    stream: bool = False,
    top_p: Optional[float] = None,
    model_id: Optional[str] = None,
    enable_thinking: Optional[bool] = False,
    reasoning_effort: Optional[str] = 'low'
) -> Dict[str, Any]:
    """
    Mock implementation of LLM API call that returns predefined responses.
    
    Args:
        messages: List of message dictionaries for the conversation
        model_name: Name of the model to use
        response_format: Desired format for the response
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens in the response
        tools: List of tool definitions for function calling
        tool_choice: How to select tools ("auto" or "none")
        api_key: Override default API key
        api_base: Override default API base URL
        stream: Whether to stream the response
        top_p: Top-p sampling parameter
        model_id: Optional ARN for Bedrock inference profiles
        enable_thinking: Whether to enable thinking
        reasoning_effort: Level of reasoning effort
        
    Returns:
        Dict[str, Any]: Mock API response
    """
    logger.info(f"Using mock LLM API call for model: {model_name}")
    
    last_user_message = None
    for message in reversed(messages):
        if message.get("role") == "user":
            last_user_message = message.get("content", "")
            break
    
    if "SEO" in str(last_user_message) or "seo" in str(last_user_message):
        return mock_seo_content_response(messages, model_name)
    elif "platform" in str(last_user_message) or "summary" in str(last_user_message):
        return mock_platform_summary_response(messages, model_name)
    else:
        return mock_general_response(messages, model_name)


def mock_seo_content_response(messages: List[Dict[str, Any]], model_name: str) -> Dict[str, Any]:
    """Generate a mock SEO content response."""
    keywords = []
    industry = "Technology"
    audience = "Professionals"
    language = "en"
    
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, str):
            if "keywords" in content.lower():
                if "AI" in content or "人工智能" in content:
                    keywords.append("AI")
                if "content marketing" in content or "内容营销" in content:
                    keywords.append("content marketing")
            if "industry" in content.lower():
                if "Technology" in content or "科技" in content:
                    industry = "Technology"
            if "audience" in content.lower():
                if "Marketing professionals" in content or "营销专业人士" in content:
                    audience = "Marketing professionals"
            if "language" in content.lower():
                if "zh" in content:
                    language = "zh"
    
    if language == "zh":
        title = "AI驱动的内容营销：未来趋势与最佳实践"
        content = """
        <h1>AI驱动的内容营销：未来趋势与最佳实践</h1>
        
        <h2>引言</h2>
        <p>随着人工智能技术的快速发展，内容营销领域正经历前所未有的变革。AI工具不仅提高了内容创作的效率，还为营销人员提供了更精准的数据分析和个性化内容推荐能力。本文将探讨AI如何重塑内容营销格局，以及营销专业人士如何利用这些技术获得竞争优势。</p>
        
        <h2>AI在内容营销中的应用</h2>
        <p>人工智能已经在内容营销的多个环节展现出强大潜力：</p>
        <ul>
            <li><strong>内容创作自动化</strong>：AI可以生成各种类型的内容，从博客文章到社交媒体帖子，大大提高了内容生产效率。</li>
            <li><strong>个性化内容推荐</strong>：通过分析用户行为数据，AI可以为不同受众提供量身定制的内容体验。</li>
            <li><strong>SEO优化</strong>：AI工具可以分析搜索趋势，提供关键词建议，并优化内容结构以提高搜索排名。</li>
            <li><strong>内容绩效分析</strong>：AI可以深入分析内容表现，提供actionable insights以优化营销策略。</li>
        </ul>
        
        <h2>AI内容营销的最佳实践</h2>
        <p>要有效利用AI进行内容营销，营销专业人士应遵循以下最佳实践：</p>
        <ol>
            <li><strong>人机协作</strong>：将AI视为增强工具而非替代品，结合人类创造力与AI效率。</li>
            <li><strong>数据驱动决策</strong>：利用AI分析工具收集和解读数据，指导内容策略制定。</li>
            <li><strong>持续学习</strong>：跟进AI技术发展，不断更新知识和技能。</li>
            <li><strong>伦理考量</strong>：确保AI应用符合隐私法规和道德标准。</li>
        </ol>
        
        <h2>未来展望</h2>
        <p>随着AI技术的不断进步，我们可以预见内容营销将变得更加智能化、个性化和高效。营销专业人士需要拥抱这一变革，将AI工具整合到日常工作流程中，以保持竞争力并取得更好的营销效果。</p>
        
        <h2>结论</h2>
        <p>AI驱动的内容营销代表了行业的未来发展方向。通过合理应用AI技术，营销专业人士可以创建更有价值的内容，提供更好的用户体验，并实现更高的ROI。现在正是拥抱AI，重新思考内容营销策略的最佳时机。</p>
        """
        meta_description = "探索AI如何革新内容营销领域，了解最新趋势和最佳实践，帮助营销专业人士提升效率和效果。"
    else:
        title = "AI-Driven Content Marketing: Future Trends and Best Practices"
        content = """
        <h1>AI-Driven Content Marketing: Future Trends and Best Practices</h1>
        
        <h2>Introduction</h2>
        <p>As artificial intelligence technology rapidly evolves, the content marketing landscape is undergoing unprecedented transformation. AI tools not only enhance content creation efficiency but also provide marketers with more precise data analysis and personalized content recommendation capabilities. This article explores how AI is reshaping the content marketing landscape and how marketing professionals can leverage these technologies to gain a competitive edge.</p>
        
        <h2>AI Applications in Content Marketing</h2>
        <p>Artificial intelligence has demonstrated tremendous potential across multiple aspects of content marketing:</p>
        <ul>
            <li><strong>Content Creation Automation</strong>: AI can generate various types of content, from blog posts to social media updates, significantly increasing content production efficiency.</li>
            <li><strong>Personalized Content Recommendations</strong>: By analyzing user behavior data, AI can deliver tailored content experiences to different audiences.</li>
            <li><strong>SEO Optimization</strong>: AI tools can analyze search trends, provide keyword suggestions, and optimize content structure to improve search rankings.</li>
            <li><strong>Content Performance Analysis</strong>: AI can deeply analyze content performance, providing actionable insights to optimize marketing strategies.</li>
        </ul>
        
        <h2>Best Practices for AI Content Marketing</h2>
        <p>To effectively utilize AI for content marketing, marketing professionals should follow these best practices:</p>
        <ol>
            <li><strong>Human-AI Collaboration</strong>: View AI as an enhancement tool rather than a replacement, combining human creativity with AI efficiency.</li>
            <li><strong>Data-Driven Decision Making</strong>: Use AI analytics tools to collect and interpret data, guiding content strategy development.</li>
            <li><strong>Continuous Learning</strong>: Stay updated on AI technology developments, constantly refreshing knowledge and skills.</li>
            <li><strong>Ethical Considerations</strong>: Ensure AI applications comply with privacy regulations and ethical standards.</li>
        </ol>
        
        <h2>Future Outlook</h2>
        <p>As AI technology continues to advance, we can anticipate content marketing becoming more intelligent, personalized, and efficient. Marketing professionals need to embrace this transformation, integrating AI tools into their daily workflows to maintain competitiveness and achieve better marketing results.</p>
        
        <h2>Conclusion</h2>
        <p>AI-driven content marketing represents the future direction of the industry. Through appropriate application of AI technology, marketing professionals can create more valuable content, provide better user experiences, and achieve higher ROI. Now is the optimal time to embrace AI and rethink content marketing strategies.</p>
        """
        meta_description = "Explore how AI is revolutionizing content marketing, learn about the latest trends and best practices to help marketing professionals improve efficiency and effectiveness."
    
    response = {
        "id": f"mock-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps({
                        "title": title,
                        "content": content,
                        "meta_description": meta_description
                    })
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 500,
            "total_tokens": 600
        }
    }
    
    return response


def mock_platform_summary_response(messages: List[Dict[str, Any]], model_name: str) -> Dict[str, Any]:
    """Generate a mock platform summary response."""
    platform = "X"
    language = "en"
    
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, str):
            if "platform" in content.lower():
                if "X" in content:
                    platform = "X"
                elif "LinkedIn" in content:
                    platform = "LinkedIn"
                elif "Medium" in content:
                    platform = "Medium"
                elif "Zhihu" in content or "知乎" in content:
                    platform = "Zhihu"
            if "language" in content.lower():
                if "zh" in content:
                    language = "zh"
    
    if platform == "X":
        if language == "zh":
            content = "AI正在彻底改变内容营销！了解如何利用人工智能提高效率、个性化内容并获得更好的ROI。#AI营销 #内容策略 #营销技术"
            hashtags = ["AI营销", "内容策略", "营销技术"]
            image_prompt = "未来派办公室场景，营销专业人士与AI助手协作创建内容"
        else:
            content = "AI is revolutionizing content marketing! Learn how to leverage artificial intelligence to improve efficiency, personalize content, and achieve better ROI. #AIMarketing #ContentStrategy #MarTech"
            hashtags = ["AIMarketing", "ContentStrategy", "MarTech"]
            image_prompt = "Futuristic office scene with marketing professionals collaborating with AI assistants to create content"
    elif platform == "LinkedIn":
        if language == "zh":
            content = "【AI驱动的内容营销：未来趋势与最佳实践】\n\n人工智能正在重塑内容营销格局。从自动化内容创作到个性化推荐，AI为营销专业人士提供了前所未有的工具和能力。\n\n我们的最新研究探讨了：\n✅ AI在内容营销中的四大应用领域\n✅ 如何实现人机协作最大化效果\n✅ 数据驱动决策的实施框架\n✅ 未来三年的技术发展预测\n\n立即阅读全文，了解如何在AI时代保持竞争优势！ #AI营销 #内容策略 #数字营销 #营销技术 #人工智能"
            hashtags = ["AI营销", "内容策略", "数字营销", "营销技术", "人工智能"]
            image_prompt = "专业商务场景，数据可视化屏幕展示AI内容营销分析"
        else:
            content = "【AI-Driven Content Marketing: Future Trends and Best Practices】\n\nArtificial intelligence is reshaping the content marketing landscape. From automated content creation to personalized recommendations, AI provides marketing professionals with unprecedented tools and capabilities.\n\nOur latest research explores:\n✅ Four key application areas of AI in content marketing\n✅ How to maximize effectiveness through human-AI collaboration\n✅ Implementation framework for data-driven decision making\n✅ Technology development forecasts for the next three years\n\nRead the full article now to learn how to maintain a competitive edge in the AI era! #AIMarketing #ContentStrategy #DigitalMarketing #MarTech #ArtificialIntelligence"
            hashtags = ["AIMarketing", "ContentStrategy", "DigitalMarketing", "MarTech", "ArtificialIntelligence"]
            image_prompt = "Professional business setting with data visualization screens showing AI content marketing analytics"
    elif platform == "Medium":
        if language == "zh":
            content = "# AI驱动的内容营销：未来趋势与最佳实践\n\n在数字化转型加速的今天，人工智能正在从根本上改变内容营销的方式。本文深入探讨了AI如何为营销专业人士提供新的机遇和挑战，以及如何利用这些技术获得竞争优势。\n\n从内容创作自动化到个性化推荐，从SEO优化到绩效分析，AI正在内容营销的各个环节展现出强大潜力。然而，成功的AI内容营销策略不仅仅依赖于技术本身，还需要人机协作、数据驱动决策和持续学习的最佳实践。\n\n阅读全文，了解如何在AI时代重新思考您的内容营销策略..."
            hashtags = ["人工智能", "内容营销", "数字营销", "营销技术", "未来趋势"]
            image_prompt = "未来主义风格的图书馆或知识中心，AI系统与人类共同创造内容"
        else:
            content = "# AI-Driven Content Marketing: Future Trends and Best Practices\n\nIn today's accelerated digital transformation, artificial intelligence is fundamentally changing how content marketing works. This article delves into how AI provides new opportunities and challenges for marketing professionals, and how to leverage these technologies for competitive advantage.\n\nFrom content creation automation to personalized recommendations, from SEO optimization to performance analysis, AI is demonstrating powerful potential across all aspects of content marketing. However, successful AI content marketing strategies rely not only on the technology itself but also on best practices in human-AI collaboration, data-driven decision making, and continuous learning.\n\nRead the full article to learn how to rethink your content marketing strategy in the AI era..."
            hashtags = ["ArtificialIntelligence", "ContentMarketing", "DigitalMarketing", "MarketingTechnology", "FutureTrends"]
            image_prompt = "Futuristic library or knowledge center with AI systems and humans co-creating content"
    elif platform == "Zhihu":
        if language == "zh":
            content = "# 如何利用AI技术提升内容营销效果？\n\n随着人工智能技术的快速发展，内容营销领域正经历前所未有的变革。作为一名营销专业人士，我发现AI不仅可以提高内容创作的效率，还能提供更精准的数据分析和个性化推荐。\n\n在实践中，我总结了几点关键经验：\n\n1. **人机协作是关键**：AI是强大的工具，但人类的创造力和情感理解仍然不可替代。最佳实践是将AI视为协作伙伴，而非替代品。\n\n2. **数据驱动决策**：利用AI分析工具收集和解读数据，指导内容策略制定。这比单纯依靠直觉效果要好得多。\n\n3. **持续学习和适应**：AI技术在不断进步，营销人员需要保持学习心态，跟进最新发展。\n\n你们在使用AI进行内容营销时有哪些经验和挑战？欢迎在评论区分享讨论。"
            hashtags = ["AI营销", "内容创作", "营销策略", "数据分析", "人工智能应用"]
            image_prompt = "现代中国办公环境，营销团队围绕显示AI分析的大屏幕讨论内容策略"
        else:
            content = "# How to Leverage AI Technology to Enhance Content Marketing Results?\n\nWith the rapid development of artificial intelligence technology, the content marketing field is experiencing unprecedented transformation. As a marketing professional, I've found that AI not only improves content creation efficiency but also provides more precise data analysis and personalized recommendations.\n\nIn practice, I've summarized several key experiences:\n\n1. **Human-AI collaboration is key**: AI is a powerful tool, but human creativity and emotional understanding remain irreplaceable. The best practice is to view AI as a collaborative partner, not a replacement.\n\n2. **Data-driven decision making**: Use AI analytics tools to collect and interpret data, guiding content strategy development. This is much more effective than relying solely on intuition.\n\n3. **Continuous learning and adaptation**: AI technology is constantly advancing, and marketers need to maintain a learning mindset to keep up with the latest developments.\n\nWhat experiences and challenges have you had when using AI for content marketing? Welcome to share and discuss in the comments section."
            hashtags = ["AIMarketing", "ContentCreation", "MarketingStrategy", "DataAnalytics", "AIApplications"]
            image_prompt = "Modern office environment with a marketing team discussing content strategy around a large screen displaying AI analytics"
    
    response = {
        "id": f"mock-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps([{
                        "platform": platform,
                        "content": content,
                        "hashtags": hashtags,
                        "image_prompt": image_prompt
                    }])
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 300,
            "total_tokens": 400
        }
    }
    
    return response


def mock_general_response(messages: List[Dict[str, Any]], model_name: str) -> Dict[str, Any]:
    """Generate a mock general response."""
    response = {
        "id": f"mock-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a mock response from the AI assistant. In a production environment, this would be generated by a real language model."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 100,
            "total_tokens": 150
        }
    }
    
    return response
