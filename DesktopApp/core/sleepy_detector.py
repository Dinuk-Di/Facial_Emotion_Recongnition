import cv2
import dlib
import time
import numpy as np

# Euclidean distance for EAR
def euclidean_distance(p1, p2):
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5

def detect_eye_aspect_ratio(eye_points):
    A = euclidean_distance(eye_points[1], eye_points[5])
    B = euclidean_distance(eye_points[2], eye_points[4])
    C = euclidean_distance(eye_points[0], eye_points[3])
    return (A + B) / (2.0 * C)

def check_sleepy(frame, ear_threshold: float = 0.25):
    """
    Detects if eyes are closed in a given frame based on EAR threshold.
    Returns True if sleepy (eyes closed), else False.
    """

    if frame is None or frame.size == 0:
        print("[Sleep Detector] Frame is empty or not captured.")
        return False

    try:
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Load face detector and predictor (load once outside in real-time apps)
        face_detector = dlib.get_frontal_face_detector()
        shape_predictor = dlib.shape_predictor("Models/shape_predictor_68_face_landmarks.dat")

        faces = face_detector(gray)

        for face in faces:
            landmarks = shape_predictor(gray, face)

            # Extract eye landmarks
            left_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(36, 42)]
            right_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(42, 48)]

            # Calculate EAR
            left_EAR = detect_eye_aspect_ratio(left_eye)
            right_EAR = detect_eye_aspect_ratio(right_eye)
            EAR = (left_EAR + right_EAR) / 2.0

            if EAR < ear_threshold:
                return True  # Eyes are likely closed

        return False  # Eyes open or no face detected

    except Exception as e:
        print(f"[Sleep Detector] Error: {e}")
        return False
