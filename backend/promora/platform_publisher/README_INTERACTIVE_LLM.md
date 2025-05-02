# 交互式LLM引导系统

## 概述

交互式LLM引导系统是一个基于GPT-4o Vision的智能页面分析和操作引导系统，专为自动化复杂网页操作流程（如账户注册、内容发布等）而设计。该系统通过分析页面截图，提供精确的操作建议，包括点击坐标、输入内容、选择选项等，实现更智能、更可靠的自动化操作。

## 主要特点

- **智能页面分析**：使用GPT-4o Vision分析页面截图，识别关键元素和操作点
- **精确坐标定位**：为每个操作提供精确的坐标位置，避免传统选择器失效的问题
- **上下文感知**：根据当前任务和平台定制分析提示词，提高分析准确性
- **人类行为模拟**：模拟真实人类操作行为，包括变速打字、随机延迟、鼠标移动等
- **多平台支持**：支持X、知乎等多个平台的注册和操作流程
- **验证码处理**：集成验证码检测和处理机制，支持人工辅助验证

## 系统组件

### 1. InteractiveLLMGuidance

核心LLM引导系统，负责分析页面截图并提供操作建议。

主要方法：
- `analyze_page`：分析整个页面并提供综合操作建议
- `analyze_element`：分析特定元素（如按钮）并提供精确坐标

### 2. InteractiveRegistration

基于交互式LLM引导的账户注册实现，用于各平台账户注册。

主要方法：
- `register_x_account`：注册X平台账户
- `_analyze_current_page`：分析当前页面
- `_execute_suggested_actions`：执行LLM建议的操作

## 使用示例

### X账户注册

```python
# 初始化交互式注册模块
interactive_registration = InteractiveRegistration(
    browser_tool=browser_tool,
    email_address=email_address,
    email_password=email_password,
    api_key=api_key
)

# 执行X账户注册
account = await interactive_registration.register_x_account(
    username="PromoraAI",
    email="test@example.com",
    password="secure_password",
    display_name="Promora AI"
)
```

## LLM分析结果示例

页面分析结果示例：

```json
{
    "page_type": "X注册流程 - 个人信息输入页面",
    "registration_step": "输入姓名和邮箱",
    "elements": [
        {
            "type": "输入框",
            "description": "姓名输入框",
            "coordinates": [640, 250],
            "is_active": true
        },
        {
            "type": "输入框",
            "description": "邮箱输入框",
            "coordinates": [640, 320],
            "is_active": false
        },
        {
            "type": "按钮",
            "description": "下一步按钮",
            "coordinates": [640, 450],
            "is_active": true
        }
    ],
    "suggested_actions": [
        {
            "type": "type",
            "target": "姓名输入框",
            "coordinates": [640, 250],
            "value": "Promora AI"
        },
        {
            "type": "type",
            "target": "邮箱输入框",
            "coordinates": [640, 320],
            "value": "test@example.com"
        },
        {
            "type": "click",
            "target": "下一步按钮",
            "coordinates": [640, 450]
        }
    ],
    "next_step": "填写生日信息"
}
```

## 调试与日志

系统会自动保存以下调试信息：
- 页面截图
- LLM分析结果
- 操作执行日志

调试信息默认保存在 `/tmp/promora_interactive_registration` 和 `/tmp/promora_llm_guidance` 目录下。

## 注意事项

- 需要设置有效的OpenAI API密钥（支持GPT-4o Vision）
- 对于需要邮箱验证的注册流程，需要提供有效的邮箱凭据
- 某些验证挑战（如复杂的CAPTCHA）可能需要人工辅助
