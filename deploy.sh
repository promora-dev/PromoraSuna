

set -e

ENV=${1:-local}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Promora 部署脚本 ==="
echo "部署环境: $ENV"

if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose 未安装"
    exit 1
fi

create_env_file() {
    if [ "$ENV" = "production" ]; then
        if [ -z "$OPENAI_API_KEY" ]; then
            echo "错误: 生产环境需要设置 OPENAI_API_KEY 环境变量"
            exit 1
        fi
        
        cat > .env << EOL
ENV_MODE=production
OPENAI_API_KEY=$OPENAI_API_KEY
MODEL_TO_USE=${MODEL_TO_USE:-gpt-4}
REDIS_PASSWORD=${REDIS_PASSWORD:-}
EOL
    else
        cp PromoraSuna/backend/.env .env 2>/dev/null || cp PromoraSuna/backend/.env.example .env
        echo "已创建本地环境文件 .env"
    fi
}

build_and_start() {
    echo "构建 Docker 镜像..."
    docker-compose build

    echo "启动服务..."
    if [ "$ENV" = "production" ]; then
        docker-compose up -d
        echo "服务已在后台启动"
    else
        docker-compose up
    fi
}

stop_services() {
    echo "停止现有服务..."
    docker-compose down || true
}

main() {
    stop_services
    create_env_file
    build_and_start
    
    if [ "$ENV" = "production" ]; then
        echo "=== 部署完成 ==="
        echo "API 地址: http://localhost:8000"
        echo "前端地址: http://localhost:3000"
        echo "使用 'docker-compose logs -f' 查看日志"
    fi
}

main
