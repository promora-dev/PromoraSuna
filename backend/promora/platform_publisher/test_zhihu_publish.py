"""
知乎文章发布测试脚本

此脚本用于测试使用提供的凭据登录知乎并发布高质量文章。
"""

import os
import sys
import time
import random
import logging
import json
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from promora.platform_publisher.platform_adapters.zhihu_adapter import ZhihuAdapter
from promora.content_generator.seo_generator import SEOContentGenerator
from services.llm import OpenAILLM

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("zhihu_test.log")
    ]
)
logger = logging.getLogger("zhihu_test")

AI_FUTURE_ARTICLE = {
    "title": "人工智能的未来发展趋势：从通用智能到人机共生",
    "content": """

在过去的十年中，人工智能技术取得了前所未有的进步。从AlphaGo战胜世界围棋冠军，到GPT系列模型展现出惊人的语言理解能力，再到DALL-E等多模态模型能够创造出令人惊叹的艺术作品，AI技术正以指数级速度发展。那么，未来十年AI将如何演变？本文将探讨人工智能的未来发展趋势，以及这些趋势将如何重塑我们的社会和经济。


当前的AI系统大多是"窄AI"，即专注于解决特定领域的问题。然而，研究界和产业界都在积极推动通用人工智能（AGI）的发展，这种AI将具备跨领域学习和解决问题的能力，更接近人类的认知水平。

最新的大型语言模型（LLM）如GPT-4已经展示出了通用智能的初步特征：

- **跨领域知识整合**：能够在医学、法律、编程等多个领域提供有价值的见解
- **上下文学习**：能够从少量示例中快速学习新任务
- **推理能力**：能够进行多步骤逻辑推理和问题解决

未来5-10年，我们可能会看到AGI的早期形态出现，这将彻底改变AI在社会中的应用方式。


未来AI系统将不再局限于单一模态（如文本或图像），而是能够无缝整合视觉、语言、声音和其他感知模态，形成真正的多模态智能。

这种融合将带来几个关键突破：

1. **更自然的人机交互**：AI将能够理解人类的面部表情、语调变化和肢体语言，使交互更加自然和情感化
2. **环境感知与理解**：AI将能够全面感知和理解复杂环境，为机器人和自动驾驶等应用提供基础
3. **创造性内容生成**：AI将能够创作跨媒体的内容，如根据文本生成视频、音乐配乐等


未来AI的发展方向不仅是替代人类，更重要的是与人类形成共生关系，增强人类能力。这种"增强智能"（IA，Intelligence Augmentation）将成为AI应用的主流范式。

具体表现为：

- **认知增强工具**：AI将成为人类思考的延伸，帮助我们处理复杂信息、发现隐藏模式、生成创新想法
- **专业技能民主化**：AI将使专业技能（如编程、设计、医疗诊断）变得更加普及，降低学习门槛
- **个性化智能助手**：每个人都将拥有深度了解自己需求和偏好的AI助手，提供全方位生活和工作支持


AI与机器人技术的结合将创造出更高级别的自主系统，能够在物理世界中执行复杂任务：

- **先进制造业机器人**：具备灵活性和适应性的机器人将重塑制造业，实现真正的智能制造
- **服务机器人普及**：从医疗护理到家庭服务，机器人将在更多领域提供服务
- **自主系统生态**：自动驾驶车辆、无人机和其他自主系统将形成互联网络，协同工作


随着AI系统变得越来越复杂和强大，可解释性和伦理问题将成为关键挑战。未来的发展趋势包括：

- **内在可解释的AI架构**：新一代AI系统将从设计上保证决策过程的透明度和可解释性
- **AI伦理标准化**：全球范围内将形成更统一的AI伦理标准和监管框架
- **价值对齐技术**：确保AI系统的目标和行为与人类价值观保持一致的技术将取得突破


当前的大型AI模型训练和运行需要消耗大量计算资源和能源。未来的发展方向将更加注重效率和可持续性：

- **模型压缩与优化**：通过知识蒸馏、量化等技术，使强大的AI能够在边缘设备上运行
- **能源效率提升**：新型硬件和算法将大幅降低AI系统的能耗
- **小样本学习**：AI将能够从少量数据中学习，减少对大规模数据集的依赖


人工智能的未来发展将不仅由技术驱动，更将由社会需求和人类价值观塑造。我们需要多方参与，共同确保AI技术朝着有益于人类福祉的方向发展。

在这个AI与人类共同进化的新时代，我们既要保持对技术潜力的乐观态度，也要对可能的风险保持警惕。通过负责任的创新和广泛的社会参与，我们有机会塑造一个AI增强人类能力、促进社会公平、推动可持续发展的未来。

人工智能的未来不是预设的命运，而是我们共同创造的结果。让我们携手迎接这个充满无限可能的未来。
    """
}

def simulate_human_typing(browser, selector, text, min_delay=0.05, max_delay=0.15):
    """模拟人类输入行为"""
    element = browser.page.locator(selector)
    element.click()
    
    element.press("Control+a")
    element.press("Backspace")
    
    for char in text:
        element.type(char, delay=random.uniform(min_delay * 1000, max_delay * 1000))
        
        if random.random() < 0.05:
            time.sleep(random.uniform(0.5, 1.5))

def simulate_human_scrolling(browser, min_scrolls=3, max_scrolls=8):
    """模拟人类滚动页面行为"""
    num_scrolls = random.randint(min_scrolls, max_scrolls)
    
    for _ in range(num_scrolls):
        scroll_distance = random.randint(100, 500)
        browser.page.evaluate(f"window.scrollBy(0, {scroll_distance})")
        
        time.sleep(random.uniform(0.5, 2.0))
    
    if random.random() < 0.3:
        browser.page.evaluate(f"window.scrollBy(0, -{random.randint(50, 200)})")
        time.sleep(random.uniform(0.5, 1.0))

def simulate_human_mouse_movement(browser, selector):
    """模拟人类鼠标移动行为"""
    element = browser.page.locator(selector)
    bbox = element.bounding_box()
    
    if not bbox:
        return
    
    offset_x = random.randint(-20, 20)
    offset_y = random.randint(-20, 20)
    browser.page.mouse.move(
        bbox["x"] + bbox["width"]/2 + offset_x,
        bbox["y"] + bbox["height"]/2 + offset_y
    )
    
    time.sleep(random.uniform(0.1, 0.3))
    
    browser.page.mouse.move(
        bbox["x"] + bbox["width"]/2,
        bbox["y"] + bbox["height"]/2
    )

def test_zhihu_article_publish():
    """测试知乎文章发布功能"""
    username = os.getenv("ZHIHU_USERNAME")
    password = os.getenv("ZHIHU_PASSWORD")
    
    if not username or not password:
        logger.error("缺少知乎账户凭据，请设置 ZHIHU_USERNAME 和 ZHIHU_PASSWORD 环境变量")
        return False
    
    logger.info("初始化知乎适配器...")
    zhihu_adapter = ZhihuAdapter(
        headless=False,  # 设置为False以便观察浏览器行为
        slow_mo=50,      # 放慢操作速度，更像人类
        timeout=60000    # 增加超时时间
    )
    
    try:
        logger.info(f"尝试登录知乎账户: {username}")
        login_result = zhihu_adapter.login(username, password)
        
        if not login_result.get("success", False):
            logger.error(f"登录失败: {login_result.get('message', '未知错误')}")
            return False
        
        logger.info("登录成功，准备发布文章...")
        
        logger.info("浏览首页...")
        zhihu_adapter.browser.page.goto("https://www.zhihu.com/")
        time.sleep(random.uniform(2, 4))
        simulate_human_scrolling(zhihu_adapter.browser)
        
        logger.info("导航到写文章页面...")
        zhihu_adapter.browser.page.goto("https://zhuanlan.zhihu.com/write")
        time.sleep(random.uniform(3, 5))
        
        logger.info(f"输入文章标题: {AI_FUTURE_ARTICLE['title']}")
        simulate_human_typing(
            zhihu_adapter.browser, 
            "input.WriteIndex-titleInput", 
            AI_FUTURE_ARTICLE["title"]
        )
        time.sleep(random.uniform(1, 2))
        
        logger.info("输入文章正文...")
        content_selector = ".public-DraftEditor-content"
        simulate_human_typing(
            zhihu_adapter.browser,
            content_selector,
            AI_FUTURE_ARTICLE["content"],
            min_delay=0.01,  # 正文较长，稍微加快速度
            max_delay=0.08
        )
        
        time.sleep(random.uniform(3, 5))
        simulate_human_scrolling(zhihu_adapter.browser, 5, 12)
        
        logger.info("点击发布按钮...")
        publish_button = "button.PublishPanel-button"
        simulate_human_mouse_movement(zhihu_adapter.browser, publish_button)
        zhihu_adapter.browser.page.click(publish_button)
        
        time.sleep(random.uniform(1, 2))
        
        logger.info("确认发布...")
        confirm_button = "button.PublishPanel-stepTwoButton"
        simulate_human_mouse_movement(zhihu_adapter.browser, confirm_button)
        zhihu_adapter.browser.page.click(confirm_button)
        
        logger.info("等待发布完成...")
        time.sleep(10)
        
        success = "发布成功" in zhihu_adapter.browser.page.content()
        
        if success:
            logger.info("文章发布成功！")
            
            current_url = zhihu_adapter.browser.page.url
            logger.info(f"文章URL: {current_url}")
            
            result = {
                "success": True,
                "platform": "zhihu",
                "account": username,
                "title": AI_FUTURE_ARTICLE["title"],
                "url": current_url,
                "timestamp": datetime.now().isoformat()
            }
            
            with open("zhihu_publish_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            return True
        else:
            logger.error("文章发布可能失败，未检测到成功提示")
            return False
            
    except Exception as e:
        logger.exception(f"测试过程中发生错误: {str(e)}")
        return False
    finally:
        logger.info("关闭浏览器...")
        zhihu_adapter.close()

if __name__ == "__main__":
    logger.info("开始知乎文章发布测试...")
    
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("未设置 OPENAI_API_KEY 环境变量，某些功能可能无法正常工作")
    
    if len(sys.argv) > 2:
        os.environ["ZHIHU_USERNAME"] = sys.argv[1]
        os.environ["ZHIHU_PASSWORD"] = sys.argv[2]
    else:
        logger.info("使用方法: python test_zhihu_publish.py <username> <password>")
        logger.info("或者设置环境变量: ZHIHU_USERNAME 和 ZHIHU_PASSWORD")
    
    success = test_zhihu_article_publish()
    
    if success:
        logger.info("测试成功完成！")
        print("\n✅ 知乎文章发布测试成功！")
    else:
        logger.error("测试失败！")
        print("\n❌ 知乎文章发布测试失败！")
