"""
知乎文章发布测试脚本

此脚本用于测试使用提供的知乎账户发布人工智能未来发展趋势文章。
"""

import os
import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime

from .test_browser_tool import TestBrowserTool
from .platform_adapters.zhihu_adapter import ZhihuAdapter
from .models import PublishRequest, PlatformAccount, PlatformType
from ..content_generator.ai_future_article import generate_ai_future_article

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("zhihu_test")

async def test_publish_zhihu_article():
    """测试发布知乎文章"""
    
    debug_dir = Path("/tmp/promora_zhihu_test")
    debug_dir.mkdir(exist_ok=True)
    
    browser_tool = TestBrowserTool(
        headless=True,   # 使用无头模式，避免需要XServer
        slow_mo=50,      # 操作之间的延迟（毫秒）
        timeout=60000,   # 默认超时时间（毫秒）
        screenshot_dir=str(debug_dir)
    )
    
    try:
        logger.info("启动浏览器...")
        await browser_tool.start()
        
        account = PlatformAccount(
            platform=PlatformType.ZHIHU,
            account_id="test_account",
            username="feng@promora.ai",
            display_name="Promora AI",
            auth_type="credentials",
            auth_data={
                "username": "feng@promora.ai",
                "password": "sv#promora0601"
            },
            status="active"
        )
        
        logger.info("创建知乎适配器...")
        zhihu_adapter = ZhihuAdapter(
            account=account,
            browser_tool=browser_tool,
            debug_dir=str(debug_dir)
        )
        
        logger.info("生成文章内容...")
        article_data = generate_ai_future_article()
        
        publish_request = PublishRequest(
            platform=PlatformType.ZHIHU,
            account_id="test_account",
            content_id=f"ai_future_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=article_data["title"],
            content=article_data["content"],
            hashtags=article_data["keywords"][:3],  # 知乎最多支持3个话题
            schedule_time=None  # 立即发布
        )
        
        logger.info("开始发布文章...")
        result = await zhihu_adapter.publish(publish_request)
        
        logger.info(f"发布结果: {result.status}")
        if result.post_url:
            logger.info(f"文章URL: {result.post_url}")
        
        if result.screenshots:
            logger.info(f"截图数量: {len(result.screenshots)}")
            for i, screenshot in enumerate(result.screenshots):
                logger.info(f"截图 {i+1}: {screenshot}")
        
        result_file = debug_dir / f"publish_result_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result.dict(), f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"结果已保存到: {result_file}")
        
        return result
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        raise
    finally:
        logger.info("关闭浏览器...")
        await browser_tool.close()

if __name__ == "__main__":
    asyncio.run(test_publish_zhihu_article())
