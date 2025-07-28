import threading
import time
from collections import deque
import cv2
import torch
import tkinter as tk
from tkinter import messagebox
import winsound

from core.human_detector import human_present
from core.sleepy_detector import check_sleepy
from core.emotion_detector import get_emotion
from core.hand_movement import detect_hand
from core.agent_system import run_agent_system


class AppController:
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_seen = time.time()
        self.agent_mode = False
        self.sleepy_mode = False
        self.eye_closed_since = None
        self.alert_triggered = False
        self.emotion_buffer = deque(maxlen=20)
        self.lock = threading.Lock()

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

        winsound.Beep(1000, 1000)
        notify()

    def run_agent_workflow(self):
        with self.lock:
            self.agent_mode = True
            print("[AGENT] Starting agent system...")
            try:
                emotion_array = list(self.emotion_buffer)
                run_agent_system(emotion_array)
            except Exception as e:
                print(f"[AGENT] Error: {e}")
            finally:
                self.agent_mode = False
                self.emotion_buffer.clear()
                print("[AGENT] Agent system finished. Resuming detectors...")

    def run(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print("[ERROR] Cannot open webcam.")
            return

        print("[INFO] GPU Available: ", torch.cuda.is_available())

        try:
            while self.running:
                if self.agent_mode:
                    time.sleep(1)  # Pause main loop while agent is running
                    continue

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

                # Run sleepy detection
                sleepy_thread = threading.Thread(target=check_sleepy, args=(frame,))
                sleepy_thread.start()
                sleepy_thread.join()

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

                if self.sleepy_mode:
                    continue
                # Run emotion + hand in parallel
                results = {"emotion": None, "hand": None}

                def run_emotion():
                    results["emotion"] = get_emotion(frame=frame)
                    print(f"[EMOTION] Detected: {results['emotion']}")

                def run_hand():
                    results["hand"] = detect_hand(frame=frame)
                    print(f"[HAND] Detected: {results['hand']}")

                t1 = threading.Thread(target=run_emotion)
                t2 = threading.Thread(target=run_hand)
                t1.start()
                t2.start()
                t1.join()
                t2.join()

                if results["emotion"] or results["hand"]:
                    # Calculate how many to add this frame
                    buffer_remaining = 20 - len(self.emotion_buffer)

                    # Estimate how many from each type
                    emotion_quota = int(buffer_remaining * 0.7)
                    hand_quota = buffer_remaining - emotion_quota

                    # Add as much as we can from available results
                    if results["emotion"] and emotion_quota > 0:
                        for _ in range(emotion_quota):
                            if len(self.emotion_buffer) < 20:
                                self.emotion_buffer.append(results["emotion"])

                    if results["hand"] and hand_quota > 0:
                        for _ in range(hand_quota):
                            if len(self.emotion_buffer) < 20:
                                self.emotion_buffer.append(results["hand"])

                    print(f"[BUFFER] Size: {len(self.emotion_buffer)} — Latest: {self.emotion_buffer[-1] } items in buffer {self.emotion_buffer}")

                # If buffer is full → start agent and pause camera
                if len(self.emotion_buffer) >= 20:
                    print("[INFO] Emotion buffer full. Starting agent system...")
                    cap.release()
                    agent_thread = threading.Thread(target=self.run_agent_workflow)
                    agent_thread.start()
                    agent_thread.join()
                    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Reopen cam after agent

                time.sleep(1)

        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("[INFO] Cleanup done. Exiting...")
