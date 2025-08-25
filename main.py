# file: main.py

import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow
import os
from PyQt5.QtGui import QFontDatabase

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # --- MEMUAT FONT KUSTOM ---
    font_dir = os.path.join(os.path.dirname(__file__), "fonts")
    if os.path.exists(font_dir):
        QFontDatabase.addApplicationFont(os.path.join(font_dir, "Poppins-Regular.ttf"))
        QFontDatabase.addApplicationFont(os.path.join(font_dir, "Poppins-Bold.ttf"))

    window = MainWindow()
    window.setMinimumSize(800, 600)   # ✅ cegah error geometry
    window.showMaximized()            # tampil fullscreen

    sys.exit(app.exec_())
