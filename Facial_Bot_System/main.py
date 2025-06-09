import sys
import threading
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt5.QtGui import QIcon
from face_detection import FaceEmotionDetector
import os
import time

def create_tray_icon():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Create system tray icon
    tray = QSystemTrayIcon()
    
    # Use fallback if icon doesn't exist
    if os.path.exists("icon.png"):
        tray.setIcon(QIcon("icon.png"))
    else:
        print("Icon not found, using default")
    
    tray.setVisible(True)
    
    # Create menu
    menu = QMenu()
    exit_action = menu.addAction("Exit")
    exit_action.triggered.connect(app.quit)
    
    tray.setContextMenu(menu)
    
    # Start face detection
    detector = FaceEmotionDetector()
    detection_thread = threading.Thread(target=detector.run)
    detection_thread.daemon = True
    detection_thread.start()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    # Wait for models to load
    print("Starting Emotion Assistant...")
    time.sleep(2)
    create_tray_icon()