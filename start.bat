@echo off
cd /d "%~dp0"

echo Starting Photo Filter Pro...
echo.

python -c "
import sys
import os
import datetime

log_file = open('app.log', 'w', encoding='utf-8')
log_file.write(f'Starting at {datetime.datetime.now()}\n')

try:
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    from photofilter.ui.gui import PhotoFilterGUI
    window = PhotoFilterGUI()
    window.show()
    
    log_file.write('GUI started\n')
    sys.exit(app.exec_())
    
except Exception as e:
    log_file.write(f'Error: {e}\n')
    import traceback
    traceback.print_exc(file=log_file)
    input('Error! Press Enter to exit...')
    sys.exit(1)
finally:
    log_file.close()
"
