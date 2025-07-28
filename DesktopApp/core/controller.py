import threading
import time
from collections import deque, Counter
import cv2
import torch
import tkinter as tk
from tkinter import messagebox
import winsound
import traceback
from queue import Queue

from core.human_detector import human_present
from core.sleepy_detector import check_sleepy
from core.emotion_detector import get_emotion
from core.hand_movement import detect_hand
from core.agent_system import run_agent_system


class AppController:
    def __init__(self,log_queue=None):
        self.log_queue = log_queue
        self.running = False
        self.thread = None
        self.last_seen = time.time()
        self.agent_mode = False
        self.sleepy_mode = False
        self.eye_closed_since = None
        self.alert_triggered = False
        self.data_buffer = deque(maxlen=60)  # 2 minutes * 60 seconds (1 sample/sec)
        self.lock = threading.Lock()
        self.window_start_time = time.time()
        self.frame_count = 0
        self.emotion_counter = Counter()
        self.hand_counter = Counter()
        self.gpu_lock = threading.Lock() 

    def start(self):
        self.running = True
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()

    def log(self, message):
        if self.log_queue:
            self.log_queue.put(message)
        print(message)  # still keep terminal logs


    def stop(self):
        self.running = False

    def buzzer_and_notify(self):
        def notify():
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning("Sleep Alert", "You appear to be asleep!")
            root.destroy()
            # Reset all states after wake up
            self.sleepy_mode = False
            self.eye_closed_since = None
            self.alert_triggered = False
            # Reset data collection
            self.data_buffer.clear()
            self.emotion_counter.clear()
            self.hand_counter.clear()
            self.window_start_time = time.time()
            self.frame_count = 0

        winsound.Beep(1000, 1000)  # 1000Hz for 1 second
        notify()

    def run_agent_workflow(self):
        with self.lock:
            print("[AGENT] Starting agent system...")
            try:
                # Convert deque to list for processing
                data_to_process = list(self.data_buffer)
                run_agent_system(data_to_process)
            except Exception as e:
                print(f"[AGENT] Error: {e}")
            finally:
                # Reset after agent finishes
                self.agent_mode = False
                self.data_buffer.clear()
                self.emotion_counter.clear()
                self.hand_counter.clear()
                self.window_start_time = time.time()
                self.frame_count = 0
                print("[AGENT] Agent system finished. Resuming detectors...")

    def run(self):
        print("[INIT] Attempting to open webcam...")
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print("[ERROR] Cannot open webcam. Trying without CAP_DSHOW...")
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("[CRITICAL] Webcam initialization failed. Exiting.")
                return

        print("[INFO] GPU Available: ", torch.cuda.is_available())

        try:
            while self.running:
                current_time = time.time()
                print(f"\n[LOOP] Frame: {self.frame_count} | Time: {current_time - self.window_start_time:.1f}s")

                # Check if 2 minutes have passed for agent execution
                if current_time - self.window_start_time >= 60:  # 120 seconds = 2 minutes
                    if not self.agent_mode and self.data_buffer:
                        print("[AGENT] Triggering agent workflow")
                        self.log("[AGENT] Triggering agent workflow")
                        self.agent_mode = True
                        print("[INFO] 2-minute window complete. Starting agent system.")
                        # Start agent in separate thread
                        agent_thread = threading.Thread(target=self.run_agent_workflow, daemon=True)
                        agent_thread.start()
                
                # Skip processing during agent execution
                if self.agent_mode:
                    print("[AGENT] Agent mode active. Sleeping...")
                    time.sleep(1)
                    continue

                # Human detection
                ret, frame = cap.read()
                if not ret:
                    print("[WARN] Empty frame received.Skipping...")
                    time.sleep(0.1)
                    continue
                    
                 # Human detection
                human_detected = human_present(frame=frame)
                print(f"[HUMAN] Detected: {human_detected}")
                self.log(f"[HUMAN] Detected: {human_detected}")

                # Check human presence
                if not human_detected:
                    time_since_seen = current_time - self.last_seen
                    print(f"[HUMAN] Not detected. Time since last: {time_since_seen:.1f}s")
                    self.log(f"[HUMAN] Not detected. Time since last: {time_since_seen:.1f}s")
                    if time_since_seen >= 30:
                        print("[HUMAN] No person for 30 seconds")
                    time.sleep(1)
                    continue
                
                self.last_seen = current_time
                self.frame_count += 1
                print(f"[PROCESSING] Frame {self.frame_count}")

                # Sleepy detection
                try:
                    eye_closed = check_sleepy(frame=frame)
                    print(f"[SLEEPY] Eye closed: {eye_closed}")
                    self.log(f"[SLEEPY] Eye closed: {eye_closed}")
                except Exception as e:
                    print(f"[SLEEPY ERROR] {e}")
                    traceback.print_exc()
                    eye_closed = False

                if eye_closed:
                    if self.eye_closed_since is None:
                        self.eye_closed_since = current_time
                        print(f"[SLEEPY] Eyes closed at {current_time}")
                        self.log(f"[SLEEPY] Eyes closed at {current_time}")
                    else:
                        closed_duration = current_time - self.eye_closed_since
                        print(f"[SLEEPY] Eyes closed for {closed_duration:.1f}s")
                        if closed_duration >= 60 and not self.alert_triggered:
                            print("[ALERT] Triggering sleep alarm")
                            self.alert_triggered = True
                            self.buzzer_and_notify()
                else:
                    self.eye_closed_since = None
                    self.alert_triggered = False

                if self.sleepy_mode:
                    print("[SLEEPY] Sleepy mode active. Skipping data collection.")
                    time.sleep(1)
                    continue

                # Run emotion + hand detection in parallel
                results = {"emotion": None, "hand": None}
                
                def run_emotion():
                    try:
                        with self.gpu_lock:
                            print("[EMOTION] Starting detection...")
                            emotion_list = get_emotion(frame=frame)
                            print(f"[EMOTION] Raw results: {emotion_list}")
                            self.log(f"[EMOTION] Raw results: {emotion_list}")
                            if emotion_list:
                                for emotion in emotion_list:
                                    if isinstance(emotion, str):
                                        self.emotion_counter[emotion] += 1
                    except Exception as e:
                        print(f"[EMOTION ERROR] {e}")
                        traceback.print_exc()

                def run_hand():
                    try:
                        print("[HAND] Starting detection...")
                        hand_list = detect_hand(frame=frame)
                        print(f"[HAND] Raw results: {hand_list}")
                        self.log(f"[HAND] Raw results: {hand_list}")
                        if hand_list:
                            for hand_result in hand_list:
                                if isinstance(hand_result, str) and hand_result != "no_hand_movement":
                                    self.hand_counter[hand_result] += 1
                    except Exception as e:
                        print(f"[HAND ERROR] {e}")
                        traceback.print_exc()

                t1 = threading.Thread(target=run_emotion)
                t2 = threading.Thread(target=run_hand)

                t1.start()
                t2.start()

                t1.join()
                t2.join()

                print(f"[COUNTERS] Emotion: {dict(self.emotion_counter)}")
                print(f"[COUNTERS] Hand: {dict(self.hand_counter)}")

                # Determine majority results every 10 frames
                if self.frame_count % 10 == 0:
                    # Get majority emotion
                    majority_emotion = None
                    if self.emotion_counter:
                        # Get most common emotion and its count
                        emotion, count = self.emotion_counter.most_common(1)[0]
                        print(f"[EMOTION] Most common: {emotion} ({count} times)")
                        # Only consider if we have at least 3 detections
                        if count >= 3:
                            majority_emotion = emotion
                    
                    # Get majority hand movement
                    majority_hand = None
                    if self.hand_counter:
                        # Get most common hand movement and its count
                        hand, count = self.hand_counter.most_common(1)[0]
                        print(f"[HAND] Most common: {hand} ({count} times)")
                        # Only consider if we have at least 2 detections
                        if count >= 2:
                            majority_hand = hand
                    
                    # Add to buffer if we have valid results
                    if majority_hand or majority_emotion:
                        if majority_hand:
                            # Prioritize hand movement if detected
                            self.data_buffer.append(majority_hand)
                            print(f"[BUFFER] Added hand movement: {majority_hand}")
                        elif majority_emotion:
                            self.data_buffer.append(majority_emotion)
                            print(f"[BUFFER] Added hand movement: {majority_hand}")
                        
                        # Reset counters
                        self.emotion_counter.clear()
                        self.hand_counter.clear()

                    # print results
                    print(f"[RESULTS] Emotion: {majority_emotion}, Hand: {majority_hand}")

                    # print full buffer status
                    print(f"[BUFFER] {self.data_buffer}")
                    
                    # Print buffer status
                    if self.data_buffer:
                        print(f"[BUFFER] Size: {len(self.data_buffer)}/{self.data_buffer.maxlen} - Last: {self.data_buffer[-1]}")
                    else:
                        print(f"[BUFFER] Size: {len(self.data_buffer)}/{self.data_buffer.maxlen}")

                time.sleep(0.5)  # Maintain ~2 FPS processing

        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("[INFO] Cleanup done. Exiting...")