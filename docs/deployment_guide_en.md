# Promora Deployment Guide

## Table of Contents
1. [Deployment Options](#deployment-options)
2. [Hardware Requirements](#hardware-requirements)
3. [Environment Testing](#environment-testing)
4. [Docker Deployment](#docker-deployment)
5. [AWS Deployment](#aws-deployment)
6. [Configuration](#configuration)
7. [Screenshot Recognition Without GPU](#screenshot-recognition-without-gpu)
8. [Troubleshooting](#troubleshooting)

## Deployment Options

Promora supports the following deployment methods:

### Local Development Environment
Suitable for development and testing, using Docker Compose to run all services on a local machine.

### Docker Container Deployment
Suitable for production environments, can be deployed on any server that supports Docker.

### Cloud Server Deployment
Deploy on cloud servers such as AWS EC2, Alibaba Cloud ECS, or Tencent Cloud CVM.

### Serverless Deployment
Deploy API services using serverless platforms like AWS Lambda or Alibaba Cloud Function Compute.

## Hardware Requirements

### Minimum Configuration
- **CPU**: 2 cores
- **Memory**: 4GB RAM
- **Storage**: 20GB SSD
- **Network**: Stable connection, at least 10Mbps

### Recommended Configuration
- **CPU**: 4 cores or higher
- **Memory**: 8GB RAM or more
- **Storage**: 50GB SSD
- **Network**: Stable connection, 50Mbps or higher

### Browser Automation Requirements
- Chrome/Chromium browser installation required
- Support for headless browser mode
- Docker environment needs appropriate resource limits

## Environment Testing

Before deployment, it's recommended to run the environment testing script to check if the system meets the requirements:

```bash
cd PromoraSuna/backend/deployment
chmod +x test_environment.sh
./test_environment.sh
```

This script checks:
- CPU cores and memory size
- Disk space
- Docker and Docker Compose installation status
- Network connectivity
- Chrome browser installation status
- Environment variable configuration

## Docker Deployment

### Using the Deployment Script

We provide a convenient deployment script that can deploy the entire application with one command:

```bash
cd PromoraSuna
chmod +x deploy.sh
./deploy.sh production
```

### Manual Deployment

If you need to deploy manually, follow these steps:

1. Clone the repository:
```bash
git clone https://github.com/promora-dev/PromoraSuna.git
cd PromoraSuna
```

2. Create environment files:
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

3. Edit the environment files to set necessary environment variables:
```bash
# In backend/.env
OPENAI_API_KEY=your_openai_api_key
MODEL_TO_USE=gpt-4
```

4. Build and start containers:
```bash
docker-compose build
docker-compose up -d
```

5. Verify that services are running properly:
```bash
docker-compose ps
```

## AWS Deployment

We provide an AWS EC2 deployment script for quick deployment on AWS EC2 instances:

```bash
cd PromoraSuna/backend/deployment
chmod +x aws_deploy.sh
./aws_deploy.sh
```

This script automatically:
1. Installs necessary system dependencies
2. Installs Docker and Docker Compose
3. Clones the repository
4. Creates environment files
5. Builds and starts containers

## Configuration

### Environment Variables

Here are the main environment variables and their descriptions:

#### Backend Environment Variables
- `ENV_MODE`: Environment mode, options are `local`, `development`, `production`
- `OPENAI_API_KEY`: OpenAI API key
- `MODEL_TO_USE`: LLM model to use, default is `gpt-4`
- `REDIS_HOST`: Redis host address
- `REDIS_PORT`: Redis port
- `REDIS_PASSWORD`: Redis password
- `REDIS_SSL`: Whether to use SSL connection to Redis

#### Frontend Environment Variables
- `NEXT_PUBLIC_API_URL`: Backend API address

### Docker Configuration

You can adjust service configurations in the `docker-compose.yaml` file:

- Adjust port mappings
- Configure volume mounts
- Set resource limits
- Configure health checks

## Screenshot Recognition Without GPU

Promora uses OpenAI's GPT-4o Vision API for screenshot recognition, which doesn't require a local GPU. Screenshots are converted to base64 format and sent to the OpenAI API, then the model returns recognition results.

### Optimization Strategies

1. **Cache Recognition Results**: For similar screenshots, cache previous recognition results to reduce API calls.

2. **Image Preprocessing**: Compress and optimize images before sending to the API to reduce data transfer.

3. **Batch Processing**: For large numbers of screenshots, use a queue system for batch processing to avoid API rate limits.

4. **Hybrid Approach**: For simple text recognition, use lightweight OCR models (like Tesseract) and only call the Vision API for complex scenarios.

### Configuration Example

Add the following configuration to the `.env` file:

```
# Screenshot Recognition Configuration
SCREENSHOT_RECOGNITION_PROVIDER=openai  # Options: openai, local_ocr, hybrid
SCREENSHOT_COMPRESSION_QUALITY=85  # Image compression quality (1-100)
SCREENSHOT_MAX_WIDTH=1200  # Maximum width, will be scaled if exceeded
ENABLE_RECOGNITION_CACHE=true  # Enable recognition result caching
```

## Troubleshooting

### Common Issues

1. **Docker Build Fails**
   - Check network connection
   - Ensure Docker daemon is running
   - Try increasing Docker resource limits

2. **Services Won't Start**
   - Check environment variable configuration
   - View container logs: `docker-compose logs -f`
   - Ensure ports are not in use

3. **Browser Automation Fails**
   - Ensure Chrome/Chromium is installed
   - Check if Playwright dependencies are completely installed
   - Increase container memory limits

4. **API Connection Timeouts**
   - Check network connection
   - Confirm API key is valid
   - Check API service provider status

### Getting Help

If you encounter problems that you cannot resolve, get help through:

- Submit an issue on the GitHub repository
- Consult the detailed documentation
- Contact the technical support team
