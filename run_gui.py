# -*- coding: utf-8 -*-
import sys
import os

print("=== Photo Filter Pro 启动 ===")
print("Python:", sys.version)

# 确保在正确目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("工作目录:", os.getcwd())

print("导入PyQt5...")
from PyQt5.QtWidgets import QApplication

print("创建应用...")
app = QApplication(sys.argv)

print("导入GUI...")
from photofilter.ui.gui import PhotoFilterGUI

print("创建窗口...")
window = PhotoFilterGUI()

print("显示窗口...")
window.show()

print("进入主循环 - 窗口应该已显示")
sys.exit(app.exec_())
