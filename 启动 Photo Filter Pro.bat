@echo off
echo ========================================
echo   Photo Filter Pro - 照片过滤器
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python
    echo 请先安装 Python 3.8+: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Install dependencies if needed
echo [1/3] 检查依赖...
pip show PyQt5 >nul 2>&1
if errorlevel 1 (
    echo [2/3] 安装依赖...
    pip install -r requirements.txt
)

REM Run the app
echo [3/3] 启动应用...
python -m photofilter.ui.gui

pause
