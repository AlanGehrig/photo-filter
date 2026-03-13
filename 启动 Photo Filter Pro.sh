#!/bin/bash
# Photo Filter Pro - 启动脚本 (macOS/Linux)

echo "========================================"
echo "  Photo Filter Pro - 照片过滤器"
echo "========================================"
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python"
    echo "请先安装 Python 3.8+: https://www.python.org/downloads/"
    exit 1
fi

# Install dependencies if needed
echo "[1/3] 检查依赖..."
if ! python3 -c "import PyQt5" 2>/dev/null; then
    echo "[2/3] 安装依赖..."
    pip3 install -r requirements.txt
fi

# Run the app
echo "[3/3] 启动应用..."
python3 -m photofilter.ui.gui
