import cv2
import time
import logging
import numpy as np
from ultralytics import YOLO
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input 
import warnings
warnings.filterwarnings('ignore')


logger = logging.getLogger(__name__)

def cleanup():
    cv2.destroyAllWindows()

def detect_hand(run_time: int = 10,
                cam_index: int = 0,
                yolo_conf: float = 0.25,
                conf_thres: float = 0.5,
                min_person_area: int = 10_000,
                frame=None):
    print("[Hand Movement Assistant] Initializing...")
    try:
        emotion_model = load_model('Models/hand_movement.h5')
    except Exception as e:
        logger.error(f"Failed to load emotion model: {e}")
        return []

    CLASS_NAMES = ['Boring', 'Neutral', 'Stress']

    try:
        model_yolo = YOLO('Models/yolov8n.pt')  # class 0 == person
    except Exception as e:
        logger.error(f"Failed to load YOLO model: {e}")
        return []

    print("[Hand Movement Assistant] Detection started...")
    emotions_window = []
    start_time = time.time()

    try:
        while time.time() - start_time < run_time:
              # Optional: flip to match user's perspective
            frame = cv2.flip(frame, 1)

            # Detect persons
            try:
                results = model_yolo(frame, classes=[0], conf=yolo_conf, verbose=False)
            except Exception as e:
                logger.warning(f"YOLO inference error: {e}")
                continue

            bbox = None
            largest_area = 0

            # Find largest person bbox
            for r in results:
                if r.boxes is None or len(r.boxes) == 0:
                    continue
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    area = (x2 - x1) * (y2 - y1)
                    if area > largest_area and area >= min_person_area:
                        largest_area = area
                        bbox = (int(x1), int(y1), int(x2 - x1), int(y2 - y1))

            if bbox:
                x, y, w, h = bbox
                cropped = frame[y:y+h, x:x+w]

                if cropped.size > 0 and w > 10 and h > 10:
                    try:
                        resized = cv2.resize(cropped, (224, 224))
                        rgb_img = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                        preprocessed = preprocess_input(rgb_img)
                        input_tensor = np.expand_dims(preprocessed, axis=0)

                        preds = emotion_model.predict(input_tensor, verbose=0)[0]
                        idx = int(np.argmax(preds))
                        conf = float(np.max(preds))

                        if conf >= conf_thres and 0 <= idx < len(CLASS_NAMES):
                            emotions_window.append(CLASS_NAMES[idx])

                    except Exception as e:
                        logger.warning(f"Emotion inference error: {e}")
                        continue

        return emotions_window

    except Exception as e:
        logger.error(f"Error during hand movement detection: {e}")
        return []
