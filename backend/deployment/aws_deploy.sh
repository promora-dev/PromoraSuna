

set -e

echo "=== Promora AWS EC2 部署脚本 ==="

if [ -z "$OPENAI_API_KEY" ]; then
    echo "错误: 缺少 OPENAI_API_KEY 环境变量"
    exit 1
fi

echo "安装系统依赖..."
sudo apt-get update
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git

echo "安装 Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    sudo usermod -aG docker $USER
    echo "Docker 安装完成"
else
    echo "Docker 已安装"
fi

echo "安装 Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.17.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose 安装完成"
else
    echo "Docker Compose 已安装"
fi

echo "克隆代码库..."
if [ ! -d "PromoraSuna" ]; then
    git clone https://github.com/promora-dev/PromoraSuna.git
    cd PromoraSuna
else
    cd PromoraSuna
    git pull
fi

echo "创建环境文件..."
cat > .env << EOL
ENV_MODE=production
OPENAI_API_KEY=$OPENAI_API_KEY
MODEL_TO_USE=${MODEL_TO_USE:-gpt-4}
REDIS_PASSWORD=${REDIS_PASSWORD:-promora_redis_password}
EOL

echo "构建和启动容器..."
docker-compose build
docker-compose up -d

echo "=== 部署完成 ==="
echo "API 地址: http://localhost:8000"
echo "前端地址: http://localhost:3000"
echo "使用 'docker-compose logs -f' 查看日志"
