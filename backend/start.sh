#!/bin/bash

# 激活虚拟环境（如果有的话）
# source venv/bin/activate

# 安装依赖
echo "Installing dependencies..."
pip install -r requirements.txt

# 设置环境变量
export MODELSCOPE_API_KEY="your_api_key_here"
export USE_GPU=0

# 运行测试（可选）
# echo "Running tests..."
# pytest tests/

# 启动系统
echo "Starting the enhanced multi-agent education system..."
uvicorn enhanced_main:app --host 0.0.0.0 --port 8000 --reload
