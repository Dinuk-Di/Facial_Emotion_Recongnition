import cv2
import time
from ultralytics import YOLO
from collections import defaultdict
from agent_system.graph import process_agent_system
import threading

class FaceEmotionDetector:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.model = YOLO("Models/best_new.pt")
        self.emotion_window = []
        self.last_process_time = time.time()
        self.class_names = ['Angry', 'Boring', 'Disgust', 'Fear', 'Happy', 'Neural', 'Sad', 'Stress', 'Suprise']

    def run(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam")
            return
            
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            for (x, y, w, h) in faces:
                face_img = frame[y:y+h, x:x+w]
                results = self.model(face_img, verbose=False)
                
                if results and results[0].probs:
                    top1_idx = results[0].probs.top1
                    emotion = self.class_names[top1_idx]
                    confidence = results[0].probs.top1conf.item()
                    
                    if confidence > 0.5:  # Confidence threshold
                        self.emotion_window.append(emotion)
            
            # Process every 10 seconds
            current_time = time.time()
            if current_time - self.last_process_time >= 10 and self.emotion_window:
                emotion_copy = self.emotion_window.copy()
                threading.Thread(
                    target=process_agent_system, 
                    args=(emotion_copy,)
                ).start()
                self.emotion_window = []
                self.last_process_time = current_time
            
            # Break condition (for development)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()