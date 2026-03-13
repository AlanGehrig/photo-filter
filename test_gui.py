import sys
import os

# 设置日志输出到文件
log_file = open("E:\\photo-filter\\gui_startup.log", "w", encoding="utf-8")

try:
    log_file.write("Starting...\n")
    log_file.flush()
    
    os.environ['QT_QPA_PLATFORM'] = 'windows'
    log_file.write("QT_QPA_PLATFORM set\n")
    log_file.flush()
    
    from PyQt5.QtWidgets import QApplication
    from PyQt5 import QtCore
    log_file.write("PyQt5 imported\n")
    log_file.flush()
    
    app = QApplication(sys.argv)
    log_file.write("QApplication created\n")
    log_file.flush()
    
    from photofilter.ui.gui import PhotoFilterGUI
    log_file.write("PhotoFilterGUI imported\n")
    log_file.flush()
    
    window = PhotoFilterGUI()
    log_file.write("Window created\n")
    log_file.flush()
    
    window.show()
    log_file.write("Window shown, entering exec loop\n")
    log_file.flush()
    
    # 运行应用
    sys.exit(app.exec_())
    
except Exception as e:
    log_file.write(f"ERROR: {e}\n")
    import traceback
    traceback.print_exc(file=log_file)
    log_file.flush()
    sys.exit(1)
finally:
    log_file.close()
