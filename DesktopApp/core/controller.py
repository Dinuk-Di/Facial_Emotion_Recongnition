import threading
import time
import cv2
import torch
import tkinter as tk
from tkinter import messagebox
import winsound
import traceback
from queue import Queue, Empty
from collections import Counter, deque
import numpy as np

from core.human_detector import human_present
from core.emotion_detector import get_emotion
from core.sleepy_detector import check_sleepy
from core.hand_movement import detect_hand
from core.agent_system import run_agent_system

class FrameReader(threading.Thread):
    def __init__(self, frame_queue):
        super().__init__(daemon=True)
        self.frame_queue = frame_queue
        self.running = True
        self.cap = None

    def run(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("[CRITICAL] Failed to initialize camera.")
            return

        while self.running:
            ret, frame = self.cap.read()
            if ret:
                if self.frame_queue.qsize() > 1:
                    self.frame_queue.get()
                self.frame_queue.put(frame)
            time.sleep(0.03)

        self.cap.release()

    def stop(self):
        self.running = False

class AppController:
    def __init__(self, log_queue=None):
        self.log_queue = log_queue
        self.frame_queue = Queue(maxsize=2)
        self.result_queue = Queue()
        self.running = False
        self.reader_thread = FrameReader(self.frame_queue)
        self.main_thread = None

        self.last_seen = time.time()
        self.eye_closed_since = None
        self.alert_triggered = False
        self.sleepy_mode = False
        self.agent_mode = False

        self.data_buffer = deque(maxlen=120)
        self.emotion_log = []
        self.hand_log = []
        self.lock = threading.Lock()
        self.gpu_lock = threading.Lock()

        self.frame_count = 0
        self.window_start_time = time.time()
        self.emotion_counter = Counter()
        self.hand_counter = Counter()

    def log(self, message):
        if self.log_queue:
            self.log_queue.put(message)
        print(message)

    def start(self):
        self.running = True
        self.reader_thread.start()
        self.main_thread = threading.Thread(target=self.run, daemon=True)
        self.main_thread.start()

    def stop(self):
        self.running = False
        self.reader_thread.stop()

    def buzzer_and_notify(self):
        def notify():
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning("Sleep Alert", "You appear to be asleep!")
            root.destroy()

        winsound.Beep(1000, 1000)
        notify()
        self.sleepy_mode = False
        self.eye_closed_since = None
        self.alert_triggered = False
        self.data_buffer.clear()

    def run_agent_workflow(self):
        with self.lock:
            self.log("[AGENT] Starting agent system...")
            # Pass only emotions as a list of strings
            # emotions = [e for e in self.emotion_log if isinstance(e, str)]
            combined_log = self.get_combined_log()
            
            self.log(f"[AGENT] Processing {len(combined_log)} events: {combined_log}")
            try:
                run_agent_system(combined_log)
            except Exception as e:
                self.log(f"[AGENT ERROR] {e}")
                traceback.print_exc()
            finally:
                self.agent_mode = False
                self.data_buffer.clear()
                self.emotion_log.clear()
                self.emotion_counter.clear()
                self.hand_counter.clear()
                self.window_start_time = time.time()
                self.frame_count = 0
                self.log("[AGENT] Finished")
                
    def get_combined_log(self):
        """Combine logs with 70% most recent emotions and 30% most recent hands"""
        # Calculate how many items to take from each log
        total_emotions = len(self.emotion_log)
        total_hands = len(self.hand_log)
        
        # If we don't have enough data, just combine what we have
        if total_emotions == 0 and total_hands == 0:
            return []
            
        # Calculate target counts based on 70/30 ratio
        n_emotions = max(1, int(total_emotions * 0.7))
        n_hands = max(1, int(total_hands * 0.3))
        
        # Get most recent items from each log
        recent_emotions = list(self.emotion_log)[-n_emotions:]
        recent_hands = list(self.hand_log)[-n_hands:]
        
        # Combine the results
        return recent_emotions + recent_hands

    def run(self):
        self.log(f"[INFO] GPU Available: {torch.cuda.is_available()}")
        try:
            while self.running:
                try:
                    frame = self.frame_queue.get(timeout=1)
                except Empty:
                    continue

                current_time = time.time()
                self.frame_count += 1

                if frame is None or frame.size == 0:
                    self.log("[WARN] Empty frame.")
                    time.sleep(1)
                    continue

                if self.agent_mode:
                    time.sleep(1)
                    
                    continue

                # Human Detection
                try:
                    detected = human_present(frame)
                    self.log(f"[Human Detection] Present: {detected}")
                except Exception as e:
                    self.log(f"[ERROR] Human detection: {e}")
                    traceback.print_exc()
                    continue

                if not detected:
                    if current_time - self.last_seen >= 30:
                        self.log("[WARN] No human detected for 30s.")
                    time.sleep(1)
                    continue

                self.last_seen = current_time

                # Sleepy Detection
                def sleepy_check():
                    try:
                        eye_closed = check_sleepy(frame)
                        self.log(f"[Sleepy] Eye closed: {eye_closed}")
                        if eye_closed:
                            if self.eye_closed_since is None:
                                self.eye_closed_since = current_time
                            elif (current_time - self.eye_closed_since >= 5) and not self.alert_triggered:
                                self.alert_triggered = True
                                self.buzzer_and_notify()
                        else:
                            self.eye_closed_since = None
                            self.alert_triggered = False
                    except Exception as e:
                        self.log(f"[ERROR] Sleepy detection: {e}")
                        traceback.print_exc()

                sleepy_thread = threading.Thread(target=sleepy_check)
                sleepy_thread.start()

                # Emotion & Hand Threads
                emotion_result, hand_result = [], []

                def detect_emotion():
                    try:
                        with self.gpu_lock:
                            emotion_result.extend(get_emotion(frame))
                    except Exception as e:
                        self.log(f"[ERROR] Emotion: {e}")

                def detect_hand_thread():
                    try:
                        hand_result.extend(detect_hand(frame))
                    except Exception as e:
                        self.log(f"[ERROR] Hand: {e}")

                t1 = threading.Thread(target=detect_emotion)
                t2 = threading.Thread(target=detect_hand_thread)
                t1.start()
                t2.start()
                t1.join()
                t2.join()

                
                if emotion_result:
                    self.log(f"[Emotion Detection] Detected: {emotion_result}")
                    self.emotion_log.extend(emotion_result)

                if hand_result:
                    self.log(f"[Hand Detection] Detected: {hand_result}")
                    self.hand_log.extend(hand_result)
                   
                self.emotion_counter.update(emotion_result)
                self.hand_counter.update(hand_result)

                if current_time - self.window_start_time >= 30 and not self.agent_mode:
                    self.agent_mode = True
                    threading.Thread(target=self.run_agent_workflow, daemon=True).start()

                time.sleep(0.2)
        finally:
            self.reader_thread.stop()
            self.log("[INFO] AppController stopped.")
            
        def add_hand_results(self, hand_results):
            """Add hand results while maintaining 70% emotion / 30% hand ratio"""
            # Calculate current composition
            total = len(self.emotion_log)
            if total == 0:
                self.emotion_log.extend(hand_results)
                return

            # Count emotion and hand entries
            emotion_count = sum(1 for item in self.emotion_log if not item.startswith('hand_'))
            hand_count = total - emotion_count
            
            # Calculate how many hand results we can add while maintaining ratio
            max_hand = int(0.3 * total)  # Max hand entries for current size
            available_slots = max(0, max_hand - hand_count)
            
            # Add only as many as we can while maintaining the ratio
            if available_slots > 0:
                to_add = hand_results[:available_slots]
                self.emotion_log.extend(to_add)
                if len(hand_results) > available_slots:
                    self.log(f"[Ratio] Added {len(to_add)} hand results (max for ratio)")
