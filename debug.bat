@echo off
cd /d "%~dp0"

echo ========================================
echo Photo Filter Pro - 诊断模式
echo ========================================
echo.

echo [1/6] 检查 Python...
python --version
echo.

echo [2/6] 检查依赖...
pip show PyQt5 pillow numpy opencv-python 2>nul | findstr /C:"Name:" /C:"Version:"
echo.

echo [3/6] 检查目录...
echo 当前目录: %CD%
echo.
dir /b *.py 2>nul
echo.

echo [4/6] 启动程序 (查看错误)...
echo.

python -c "
import sys
import os
import traceback
import datetime

print('[DEBUG] Starting...')

try:
    print('[DEBUG] Importing PyQt5...')
    from PyQt5.QtWidgets import QApplication
    print('[DEBUG] PyQt5 imported')
    
    print('[DEBUG] Creating QApplication...')
    app = QApplication(sys.argv)
    print('[DEBUG] QApplication created')
    
    print('[DEBUG] Importing GUI...')
    from photofilter.ui.gui import PhotoFilterGUI
    print('[DEBUG] GUI imported')
    
    print('[DEBUG] Creating window...')
    window = PhotoFilterGUI()
    print('[DEBUG] Window created')
    
    print('[DEBUG] Showing window...')
    window.show()
    print('[DEBUG] Window shown')
    
    print('[OK] 程序启动成功!')
    print('[OK] 如果看到窗口，请关闭它继续...')
    
    # 不退出，让用户看到结果
    import time
    time.sleep(3)
    
    app.quit()
    print('[DONE] Exiting normally')
    
except Exception as e:
    print(f'[ERROR] {e}')
    traceback.print_exc()
    input('按回车键退出...')
"
