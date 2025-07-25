import cv2
import time
import logging
from ultralytics import YOLO

logger = logging.getLogger(__name__)

def cleanup():
    cv2.destroyAllWindows()

def get_emotion(run_time=10, conf_thres=0.5, cam_index=0):
    """
    Captures webcam frames, detects faces, predicts emotions,
    and returns an array of predicted emotions over `run_time` seconds.
    """
    face_detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    model = YOLO("Models/best_new.pt")
    class_names = ['Angry', 'Boring', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Stress', 'Suprise']

    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        logger.error("Camera error.")
        return []

    print("[Emotion Assistant] Detection started...")
    emotion_window = []
    start_time = time.time()

    try:
        while time.time() - start_time < run_time:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, 1.1, 4)

            for (x, y, w, h) in faces:
                face_img = frame[y:y+h, x:x+w]
                try:
                    results = model(face_img, verbose=False)
                    probs = getattr(results[0], "probs", None)
                    if probs is not None:
                        top1_idx = probs.top1
                        confidence = float(probs.top1conf)
                        if 0 <= top1_idx < len(class_names) and confidence > conf_thres:
                            emotion_window.append(class_names[top1_idx])
                except Exception as e:
                    logger.warning(f"Model error: {e}")

        return emotion_window

    finally:
        cap.release()
        cleanup()

