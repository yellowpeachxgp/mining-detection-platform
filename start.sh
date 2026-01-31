#!/bin/bash

# 设置字符编码
export LANG=en_US.UTF-8

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  露天矿区损毁与复垦检测平台 - Linux/Mac启动脚本     ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# 检查Python
echo "[1/2] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未找到"
    echo "请先安装: brew install python3 (Mac) 或 apt install python3 (Linux)"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✓ $PYTHON_VERSION 已找到"

# 检查依赖
echo ""
echo "[2/2] 检查Python依赖..."
python3 -c "import flask, numpy, rasterio; print('✓ 核心依赖已安装')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠ 检测到缺少依赖，正在安装..."
    cd "$(dirname "$0")/backend"
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
fi

# 启动应用
echo ""
echo "启动Flask应用..."
cd "$(dirname "$0")/backend"
echo "📍 工作目录: $(pwd)"
echo "🌐 访问地址: http://127.0.0.1:5000"
echo "💡 按 Ctrl+C 停止服务"
echo ""
echo "═════════════════════════════════════════════════════════"
echo ""

python3 run_app.py
