

set -e

echo "=== Promora 环境测试脚本 ==="

echo "检查系统资源..."
CPU_CORES=$(grep -c ^processor /proc/cpuinfo)
TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
DISK_SPACE=$(df -h / | awk 'NR==2 {print $4}')

echo "CPU 核心数: $CPU_CORES"
echo "内存总量: ${TOTAL_MEM}MB"
echo "可用磁盘空间: $DISK_SPACE"

if [ $CPU_CORES -lt 2 ]; then
    echo "警告: CPU 核心数低于推荐值 (2)"
fi

if [ $TOTAL_MEM -lt 4000 ]; then
    echo "警告: 内存总量低于推荐值 (4000MB)"
fi

echo "检查 Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "Docker 已安装: $DOCKER_VERSION"
else
    echo "错误: Docker 未安装"
    exit 1
fi

echo "检查 Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo "Docker Compose 已安装: $COMPOSE_VERSION"
else
    echo "错误: Docker Compose 未安装"
    exit 1
fi

echo "检查网络连接..."
if ping -c 1 google.com &> /dev/null; then
    echo "网络连接正常"
else
    echo "警告: 无法连接到互联网"
fi

echo "检查 Chrome 浏览器..."
if command -v google-chrome &> /dev/null || command -v google-chrome-stable &> /dev/null; then
    CHROME_VERSION=$(google-chrome --version 2>/dev/null || google-chrome-stable --version)
    echo "Chrome 已安装: $CHROME_VERSION"
else
    echo "警告: Chrome 未安装"
fi

echo "检查环境变量..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "警告: OPENAI_API_KEY 环境变量未设置"
else
    echo "OPENAI_API_KEY 已设置"
fi

echo "=== 环境测试完成 ==="
