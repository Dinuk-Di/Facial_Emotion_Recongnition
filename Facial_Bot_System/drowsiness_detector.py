import cv2
import dlib
import time
import threading
import numpy as np

class DrowsinessDetector:
    def _init_(self, status_ui=None):
        self.status_ui = status_ui
        self.running = True
        self.eye_ar_threshold = 0.25
        self.closed_duration_threshold = 10  # seconds
        
        # Initialize models
        self.face_detector = dlib.get_frontal_face_detector()
        self.dlib_facelandmark = dlib.shape_predictor(
            "shape_predictor_68_face_landmarks.dat"
        )
        
        # State variables
        self.closed_eye_start_time = None
        self.alert_triggered = False
        self.status_message = "Monitoring..."
        self.last_status_update = 0

    def euclidean_distance(self, point1, point2):
        return np.sqrt((point1[0] - point2[0])*2 + (point1[1] - point2[1])*2)

    def detect_eye(self, eye_points):
        poi_A = self.euclidean_distance(eye_points[1], eye_points[5])
        poi_B = self.euclidean_distance(eye_points[2], eye_points[4])
        poi_C = self.euclidean_distance(eye_points[0], eye_points[3])
        return (poi_A + poi_B) / (2 * poi_C)

    def speak_alert(self, message):
        # This would be implemented with your TTS system
        if self.status_ui:
            self.status_ui.show_alert(message)

    def process_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector(gray)
        current_time = time.time()
        
        if not faces:
            self.closed_eye_start_time = None
            self.alert_triggered = False
            self.status_message = "No face detected"
            return
        
        for face in faces:
            landmarks = self.dlib_facelandmark(gray, face)
            left_eye = []
            right_eye = []

            # Right eye (points 42-47)
            for n in range(42, 48):
                x = landmarks.part(n).x
                y = landmarks.part(n).y
                right_eye.append((x, y))
            
            # Left eye (points 36-41)
            for n in range(36, 42):
                x = landmarks.part(n).x
                y = landmarks.part(n).y
                left_eye.append((x, y))
            
            # Calculate eye aspect ratio
            right_ear = self.detect_eye(right_eye)
            left_ear = self.detect_eye(left_eye)
            eye_ar = (left_ear + right_ear) / 2
            
            # Drowsiness detection logic
            if eye_ar < self.eye_ar_threshold:
                if self.closed_eye_start_time is None:
                    self.closed_eye_start_time = current_time
                    self.status_message = "Eyes closed - Timing..."
                else:
                    closed_duration = current_time - self.closed_eye_start_time
                    
                    if closed_duration >= self.closed_duration_threshold and not self.alert_triggered:
                        self.alert_triggered = True
                        self.status_message = "ALERT! Drowsiness detected!"
                        threading.Thread(target=self.speak_alert, 
                                        args=("Wake up! Drowsiness detected!",)).start()
            else:
                if self.closed_eye_start_time is not None:
                    self.closed_eye_start_time = None
                    self.alert_triggered = False
                    self.status_message = "Eyes open - Good to go!"
        
        # Update status UI
        if self.status_ui:
            self.status_ui.update_drowsiness_status(
                status=self.status_message,
                duration=(time.time() - self.closed_eye_start_time) if self.closed_eye_start_time else 0
            )

    def stop(self):
        self.running = False