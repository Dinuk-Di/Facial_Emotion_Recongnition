
# import sys
# import os
# import time
# import threading
# from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu
# from PyQt5.QtGui import QIcon
# from face_detection import FaceEmotionDetector
# # from drowsiness_detector import DrowsinessDetector
# from ui.status_ui import AgentStatusUI

# def create_tray_icon():
#     app = QApplication(sys.argv)
#     app.setQuitOnLastWindowClosed(False)

#     tray = QSystemTrayIcon(QIcon("icon.png") if os.path.exists("icon.png") else QIcon())
#     tray.setVisible(True)

#     # UI window for status
#     status_ui = AgentStatusUI()
#     status_ui.show()

#     # Detection logic
#     detector = FaceEmotionDetector()
#     # drowsiness_detector = DrowsinessDetector()
#     detector.status_ui = status_ui 

#     # Thread
#     detection_thread = threading.Thread(target=detector.run, daemon=True)
#     # drowsiness_thread = threading.Thread(target=drowsiness_detector.run, daemon=True)
#     detection_thread.start()
#     # drowsiness_thread.start()

#     # Menu
#     menu = QMenu()
#     restart_action = menu.addAction("Restart")
#     restart_action.triggered.connect(lambda: os.execl(sys.executable, sys.executable, *sys.argv))
#     exit_action = menu.addAction("Exit")
#     exit_action.triggered.connect(app.quit)
#     tray.setContextMenu(menu)

#     sys.exit(app.exec_())

# if __name__ == "__main__":
#     print("Starting Emotion Assistant...")
#     time.sleep(1)
#     create_tray_icon()


import tkinter as tk
from win10toast import ToastNotifier

# List of emotions and emojis
emotions = [
    ("Happy", "😊"),
    ("Sad", "😢"),
    ("Excited", "🤩"),
    ("Angry", "😠"),
    ("Calm", "😌"),
]
current = [0]  # Index tracker

def next_emotion():
    current[0] = (current[0] + 1) % len(emotions)
    emotion_label.config(text=f"{emotions[current[0]][1]} {emotions[current[0]][0]}")

def send_notification():
    toaster = ToastNotifier()
    emoji, emotion = emotions[current[0]]
    toaster.show_toast("Emotion Notification", f"Current emotion: {emotion} {emoji}", duration=5)

root = tk.Tk()
root.overrideredirect(True)  # Borderless
root.attributes("-topmost", True)
root.configure(bg="#ffe066")  # Custom background

# Get screen dimensions and set initial size
w, h = 200, 130
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
root.geometry(f"{w}x{h}+{screen_w-w-10}+{screen_h-h-60}")

# Frame for emotion display
panel = tk.Frame(root, bg="#ffd23f")
panel.pack(fill="x", pady=(10,0))
emotion_label = tk.Label(panel, text=f"{emotions[0][1]} {emotions[0][0]}", font=("Segoe UI Emoji", 22, "bold"), bg="#ffd23f")
emotion_label.pack()

# Buttons frame
btn_frame = tk.Frame(root, bg="#ffe066")
btn_frame.pack(fill="x", pady=(8,12))

# Switch emotion
next_btn = tk.Button(btn_frame, text="Next Emotion", font=("Segoe UI", 10, "bold"),
                     bg="#70c1b3", fg="white", command=next_emotion, relief="raised")
next_btn.pack(padx=10, pady=2, fill="x")

# Notification button
notif_btn = tk.Button(btn_frame, text="Send Notification", font=("Segoe UI", 10, "bold"),
                      bg="#b2dbbf", fg="#333", command=send_notification, relief="raised")
notif_btn.pack(padx=10, pady=2, fill="x")

# Exit button (optional)
exit_btn = tk.Button(btn_frame, text="Close", font=("Segoe UI", 10),
                     bg="#f48b29", fg="white", command=root.destroy, relief="flat")
exit_btn.pack(padx=10, pady=(8,0), fill="x")

root.mainloop()