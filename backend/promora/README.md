# Promora - AI 驱动的虚拟首席市场官

Promora 是一个 AI 驱动的虚拟首席市场官平台，为企业提供全自动内容营销和 SEO 增长解决方案。本项目基于 PromoraSuna 代码库开发，融合了 GPT-4、Playwright、GPT-4o Vision、NoVNC 等技术。

## 功能特点

- **高质量内容生成**：基于 GPT-4，自动生成 SEO 优化内容与平台适配摘要
- **多平台分发支持**：覆盖知乎、X、LinkedIn、Medium 等平台
- **多账号矩阵运营**：每个平台支持管理多个账号，话题/语言差异化运营
- **智能调度机制**：定时发布、失败自动重试、发布状态追踪
- **数据回流分析**：自动追踪互动、点击、排名等指标，辅助优化内容策略

## 系统架构

Promora 系统由以下主要模块组成：

1. **内容生成模块** (`content_generator`)
   - SEO 内容生成
   - 多平台摘要生成
   - 多语言支持

2. **平台发布模块** (`platform_publisher`)
   - 平台适配器 (X, LinkedIn, Medium, 知乎)
   - 发布状态追踪
   - 失败重试机制

3. **任务调度模块** (`task_scheduler`)
   - 任务定义与执行
   - 定时发布
   - 任务状态管理

4. **数据分析模块** (`analytics`)
   - 内容表现分析
   - 关键词排名追踪
   - 账号表现分析

5. **API 接口** (`api`)
   - RESTful API 接口
   - 依赖注入
   - 错误处理

## 技术实现

- 使用 FastAPI 构建后端 API
- 利用 Playwright 实现浏览器自动化
- 通过 SandboxBrowserTool 实现浏览器操作
- 集成 GPT-4 进行内容生成
- 使用 NoVNC 可视化 AI 操作过程

## 使用方法

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 启动服务：
   ```bash
   python main.py
   ```

3. 访问 API 文档：
   ```
   http://localhost:8000/docs
   ```

## MVP 范围

当前实现的 MVP 功能包括：

- 关键词驱动的 SEO 文章与摘要生成
- 自动发布到 X、LinkedIn、Medium
- Playwright 实现知乎平台发文
- NoVNC 展示 AI 自动执行过程
- 发文成功状态与失败重试机制

## 后续规划

1. 支持图文混排与内容模板化
2. 引入 GPT Agent 自动构建关键词与话题库
3. 引导式内容创作（表单式流程）
4. SaaS 企业部署方案（多账户 + 团队协作）
5. 全流程操作录像、内容归档、资产管理
