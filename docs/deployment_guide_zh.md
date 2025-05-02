# Promora 部署指南

## 目录
1. [部署选项](#部署选项)
2. [硬件要求](#硬件要求)
3. [环境测试](#环境测试)
4. [Docker 部署](#docker-部署)
5. [AWS 部署](#aws-部署)
6. [配置说明](#配置说明)
7. [无 GPU 环境下的截图识别](#无-gpu-环境下的截图识别)
8. [故障排除](#故障排除)

## 部署选项

Promora 支持以下部署方式：

### 本地开发环境
适用于开发和测试，使用 Docker Compose 在本地机器上运行所有服务。

### Docker 容器部署
适用于生产环境，可以在任何支持 Docker 的服务器上部署。

### 云服务器部署
在 AWS EC2、阿里云 ECS 或腾讯云 CVM 等云服务器上部署。

### Serverless 部署
使用 AWS Lambda、阿里云函数计算等无服务器平台部署 API 服务。

## 硬件要求

### 最低配置
- **CPU**: 2 核心
- **内存**: 4GB RAM
- **存储**: 20GB SSD
- **网络**: 稳定连接，至少 10Mbps

### 推荐配置
- **CPU**: 4 核心或更高
- **内存**: 8GB RAM 以上
- **存储**: 50GB SSD
- **网络**: 稳定连接，50Mbps 以上

### 浏览器自动化要求
- 需要安装 Chrome/Chromium 浏览器
- 支持无头浏览器模式
- Docker 环境需配置适当的资源限制

## 环境测试

在部署前，建议运行环境测试脚本检查系统是否满足要求：

```bash
cd PromoraSuna/backend/deployment
chmod +x test_environment.sh
./test_environment.sh
```

该脚本会检查：
- CPU 核心数和内存大小
- 磁盘空间
- Docker 和 Docker Compose 安装状态
- 网络连接
- Chrome 浏览器安装状态
- 环境变量配置

## Docker 部署

### 使用部署脚本

我们提供了一个简便的部署脚本，可以一键部署整个应用：

```bash
cd PromoraSuna
chmod +x deploy.sh
./deploy.sh production
```

### 手动部署

如果需要手动部署，可以按照以下步骤操作：

1. 克隆代码库：
```bash
git clone https://github.com/promora-dev/PromoraSuna.git
cd PromoraSuna
```

2. 创建环境文件：
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

3. 编辑环境文件，设置必要的环境变量：
```bash
# 在 backend/.env 中设置
OPENAI_API_KEY=your_openai_api_key
MODEL_TO_USE=gpt-4
```

4. 构建和启动容器：
```bash
docker-compose build
docker-compose up -d
```

5. 验证服务是否正常运行：
```bash
docker-compose ps
```

## AWS 部署

我们提供了 AWS EC2 部署脚本，可以在 AWS EC2 实例上快速部署：

```bash
cd PromoraSuna/backend/deployment
chmod +x aws_deploy.sh
./aws_deploy.sh
```

该脚本会自动：
1. 安装必要的系统依赖
2. 安装 Docker 和 Docker Compose
3. 克隆代码库
4. 创建环境文件
5. 构建和启动容器

## 配置说明

### 环境变量

以下是主要的环境变量及其说明：

#### 后端环境变量
- `ENV_MODE`: 环境模式，可选值为 `local`、`development`、`production`
- `OPENAI_API_KEY`: OpenAI API 密钥
- `MODEL_TO_USE`: 使用的 LLM 模型，默认为 `gpt-4`
- `REDIS_HOST`: Redis 主机地址
- `REDIS_PORT`: Redis 端口
- `REDIS_PASSWORD`: Redis 密码
- `REDIS_SSL`: 是否使用 SSL 连接 Redis

#### 前端环境变量
- `NEXT_PUBLIC_API_URL`: 后端 API 地址

### Docker 配置

可以在 `docker-compose.yaml` 文件中调整服务配置：

- 调整端口映射
- 配置卷挂载
- 设置资源限制
- 配置健康检查

## 无 GPU 环境下的截图识别

Promora 使用 OpenAI 的 GPT-4o Vision API 进行截图识别，不需要本地 GPU。截图会被转换为 base64 格式并发送到 OpenAI API，然后模型返回识别结果。

### 优化策略

1. **缓存识别结果**：对于相似的截图，缓存之前的识别结果以减少 API 调用。

2. **图像预处理**：在发送到 API 前对图像进行压缩和优化，减少传输数据量。

3. **分批处理**：对于大量截图，使用队列系统分批处理，避免 API 限流。

4. **混合方法**：对于简单的文本识别，可以使用轻量级的 OCR 模型（如 Tesseract），只在复杂场景下调用 Vision API。

### 配置示例

在 `.env` 文件中添加以下配置：

```
# 截图识别配置
SCREENSHOT_RECOGNITION_PROVIDER=openai  # 可选: openai, local_ocr, hybrid
SCREENSHOT_COMPRESSION_QUALITY=85  # 图像压缩质量 (1-100)
SCREENSHOT_MAX_WIDTH=1200  # 最大宽度，超过会被缩放
ENABLE_RECOGNITION_CACHE=true  # 启用识别结果缓存
```

## 故障排除

### 常见问题

1. **Docker 构建失败**
   - 检查网络连接
   - 确保 Docker 守护进程正在运行
   - 尝试增加 Docker 资源限制

2. **服务无法启动**
   - 检查环境变量配置
   - 查看容器日志：`docker-compose logs -f`
   - 确保端口未被占用

3. **浏览器自动化失败**
   - 确保已安装 Chrome/Chromium
   - 检查 Playwright 依赖是否完整安装
   - 增加容器内存限制

4. **API 连接超时**
   - 检查网络连接
   - 确认 API 密钥是否有效
   - 检查 API 服务提供商状态

### 获取帮助

如果遇到无法解决的问题，请通过以下方式获取帮助：

- 在 GitHub 仓库提交 Issue
- 查阅详细的文档
- 联系技术支持团队
