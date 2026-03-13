@echo off
cd /d "%~dp0"
title Photo Filter Pro

echo Starting Photo Filter Pro...
echo.

:: 直接运行Python，不等待输出
start "" pythonw.exe run_gui.py

:: 等待一下让窗口启动
timeout /t 2 /nobreak >nul

echo 程序已启动！
pause
