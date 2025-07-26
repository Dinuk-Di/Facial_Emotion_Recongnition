import threading
import time
from core.human_detector import human_present
from core.sleepy_detector import check_sleepy
from core.emotion_detector import get_emotion
from core.hand_movement import detect_hand
from core.agent_system import run_agent_system
import cv2
import torch
import tkinter as tk
from tkinter import messagebox
import winsound

class AppController:
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_seen = time.time()
        self.agent_mode = False
        self.eye_closed_since = None
        self.alert_triggered = False
        self.sleepy_mode = False

    def start(self):  
        self.running = True  
        if self.thread is None or not self.thread.is_alive():  
            self.thread = threading.Thread(target=self.run, daemon=True)  
            self.thread.start()  

    def stop(self):  
        self.running = False  

    def buzzer_and_notify(self):  
        def notify():  
            root = tk.Tk()  
            root.withdraw()  
            messagebox.showwarning("Sleep Alert", "You appear to be asleep!")  
            root.destroy()  
            self.sleepy_mode = False  
            self.eye_closed_since = None  

        winsound.Beep(1000, 1000)  # 1kHz for 1 sec  
        notify()  

    def run(self):  
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  
        if not cap.isOpened():  
            print("[ERROR] Cannot open webcam.")  
            return  

        print("[INFO] GPU Available: ", torch.cuda.is_available())  

        try:  
            while self.running:  
                ret, frame = cap.read()  
                if not ret:  
                    print("[WARN] Empty frame received.")  
                    continue  

                if not human_present(frame=frame):  
                    if time.time() - self.last_seen >= 300:  
                        print("[INFO] No person detected for 5 mins.")  
                        time.sleep(5)  
                    continue  

                self.last_seen = time.time()  

                # Sleepy check (always run)  
                eye_closed = check_sleepy(frame=frame)  
                if eye_closed:  
                    if self.eye_closed_since is None:  
                        self.eye_closed_since = time.time()  
                    elif time.time() - self.eye_closed_since >= 10 and not self.sleepy_mode:  
                        print("[ALERT] Eye closed for 10s. Triggering alarm.")  
                        self.sleepy_mode = True  
                        self.buzzer_and_notify()  
                else:  
                    self.eye_closed_since = None  

                # If sleepy, pause detection  
                if self.sleepy_mode:  
                    continue  

                # Run parallel detectors  
                results = {"emotion": None, "hand": None}  

                def run_emotion():  
                    results["emotion"] = get_emotion(frame=frame)  

                def run_hand():  
                    results["hand"] = detect_hand(frame=frame)  

                t1 = threading.Thread(target=run_emotion)  
                t2 = threading.Thread(target=run_hand)  

                t1.start()  
                t2.start()  
                t1.join()  
                t2.join()  

                print(f"[RESULT] Emotion: {results['emotion']}")  
                print(f"[RESULT] Hand Movement: {results['hand']}")  

                time.sleep(1)  

        finally:  
            cap.release()  
            cv2.destroyAllWindows()  
            print("[INFO] Cleanup done. Exiting...")  
