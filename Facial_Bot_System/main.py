import sys
import os
import time
import threading
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt5.QtGui import QIcon
from face_detection import FaceEmotionDetector
from ui.status_ui import AgentStatusUI

def create_tray_icon():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray = QSystemTrayIcon(QIcon("icon.png") if os.path.exists("icon.png") else QIcon())
    tray.setVisible(True)

    # UI window for status
    # status_ui = AgentStatusUI()
    # status_ui.show()

    # Detection logic
    detector = FaceEmotionDetector()
    # detector.status_ui = status_ui 

    # Thread
    detection_thread = threading.Thread(target=detector.run, daemon=True)
    detection_thread.start()

    # Menu
    menu = QMenu()
    restart_action = menu.addAction("Restart")
    restart_action.triggered.connect(lambda: os.execl(sys.executable, sys.executable, *sys.argv))
    exit_action = menu.addAction("Exit")
    exit_action.triggered.connect(app.quit)
    tray.setContextMenu(menu)

    sys.exit(app.exec_())

if __name__ == "__main__":
    print("Starting Emotion Assistant...")
    time.sleep(1)
    create_tray_icon()
