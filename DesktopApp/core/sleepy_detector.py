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

def check_sleepy(run_time: int = 10, 
                 ear_threshold: float = 0.25, 
                 close_duration: float = 3.0, 
                 cam_index: int = 0):
    """
    Checks if the person appears sleepy by monitoring eye closure.
    Returns True if eyes are closed for >= close_duration seconds 
    during the observation window of run_time seconds.
    """

    # Load face detector & shape predictor
    face_detector = dlib.get_frontal_face_detector()
    shape_predictor = dlib.shape_predictor(
        "Models/shape_predictor_68_face_landmarks.dat"
    )

    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        print("[Sleep Detector] Camera not available.")
        return False

    start_time = time.time()
    closed_eye_start = None
    sleepy_detected = False

    try:
        while time.time() - start_time < run_time:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector(gray)

            if not faces:
                closed_eye_start = None
                continue

            for face in faces:
                landmarks = shape_predictor(gray, face)

                # Extract eye points
                left_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(36, 42)]
                right_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(42, 48)]

                # Compute EAR
                left_EAR = detect_eye_aspect_ratio(left_eye)
                right_EAR = detect_eye_aspect_ratio(right_eye)
                EAR = (left_EAR + right_EAR) / 2.0

                # Check if eyes are closed
                if EAR < ear_threshold:
                    if closed_eye_start is None:
                        closed_eye_start = time.time()
                    else:
                        if time.time() - closed_eye_start >= close_duration:
                            sleepy_detected = True
                            return True  # Early return if detected
                else:
                    closed_eye_start = None

        return sleepy_detected

    finally:
        cap.release()
        cv2.destroyAllWindows()
