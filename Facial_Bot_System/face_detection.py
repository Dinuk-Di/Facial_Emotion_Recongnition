import cv2
import time
import threading
import signal
import queue
import sys
import logging
from ultralytics import YOLO
from collections import defaultdict
from agent_system.graph import process_agent_system

logger = logging.getLogger(__name__)

class FaceEmotionDetector:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.model = YOLO(r"F:\Academic\7th semester\FYP\recommondation_agents_implementation\models\best_new.pt")
        self.class_names = ['Angry', 'Boring', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Stress', 'Suprise']
        self.emotion_window = []
        self.last_process_time = time.time()
        self.processing_active = False
        self.agent_queue = queue.Queue()
        self.status_ui = None
        signal.signal(signal.SIGINT, self.handle_interrupt)

    def handle_interrupt(self, sig, frame):
        print("\n[Emotion Assistant] Ctrl+C detected. Shutting down...")
        self.cleanup()

    def cleanup(self):
        cv2.destroyAllWindows()
        sys.exit(0)

    def run_agent_system(self, emotions):
        try:
            final_state = process_agent_system(emotions)
            print("final state in face_detection :", final_state)
            if self.status_ui:
                self.status_ui.update_status(
                    emotion=final_state.average_emotion,
                    # detected_task=final_state.detected_task,
                    recommendation=final_state.recommendation,
                    executed=final_state.executed
                )
        except Exception as e:
            logger.error(f"Agent error: {e}")
        finally:
            self.agent_queue.put(True)

    def run(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logger.error("Camera error.")
            return

        print("[Emotion Assistant] Detection started...")
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

            for (x, y, w, h) in faces:
                face_img = frame[y:y + h, x:x + w]
                try:
                    results = self.model(face_img, verbose=False)
                    if results and results[0].probs:
                        top1_idx = results[0].probs.top1
                        confidence = results[0].probs.top1conf.item()
                        if 0 <= top1_idx < len(self.class_names) and confidence > 0.5:
                            self.emotion_window.append(self.class_names[top1_idx])
                except Exception as e:
                    logger.warning(f"Model error: {e}")

            if self.processing_active and not self.agent_queue.empty():
                self.agent_queue.get()
                self.processing_active = False

            if time.time() - self.last_process_time >= 10 and self.emotion_window and not self.processing_active:
                emotions_copy = self.emotion_window.copy()
                self.emotion_window.clear()
                self.last_process_time = time.time()
                self.processing_active = True
                threading.Thread(target=self.run_agent_system, args=(emotions_copy,), daemon=True).start()

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        self.cleanup()
