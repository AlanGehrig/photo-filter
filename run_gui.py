# -*- coding: utf-8 -*-
import sys
import os
import traceback
import datetime

print("=== Photo Filter Pro Diagnostic ===")
print(f"Time: {datetime.datetime.now()}")
print(f"Python: {sys.version}")
print(f"Work dir: {os.getcwd()}")

log_file = open('app.log', 'w', encoding='utf-8')
log_file.write("=== Photo Filter Pro ===\n")

try:
    print("\n[1] Import PyQt5...")
    from PyQt5.QtWidgets import QApplication
    print("    OK - PyQt5 imported")
    log_file.write("PyQt5 OK\n")
    
    print("[2] Create QApplication...")
    app = QApplication(sys.argv)
    print("    OK - QApplication created")
    log_file.write("QApplication OK\n")
    
    print("[3] Import GUI...")
    from photofilter.ui.gui import PhotoFilterGUI
    print("    OK - GUI imported")
    log_file.write("GUI import OK\n")
    
    print("[4] Create window...")
    window = PhotoFilterGUI()
    print("    OK - Window created")
    log_file.write("Window created OK\n")
    
    print("[5] Show window...")
    window.show()
    print("    OK - Window shown")
    log_file.write("Window show OK\n")
    
    print("\n=== SUCCESS! ===")
    log_file.write("SUCCESS\n")
    log_file.close()
    
    sys.exit(app.exec_())
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    traceback.print_exc()
    log_file.write(f"ERROR: {e}\n")
    traceback.print_exc(file=log_file)
    log_file.close()
    input("\nError! Press Enter...")
    sys.exit(1)
