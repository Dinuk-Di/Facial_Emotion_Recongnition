import cv2
import time
import logging
from functools import lru_cache
from ultralytics import YOLO

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def _load_yolo(model_path: str = "Models/yolov8n.pt"):
    """Load once and cache the YOLO model (fast subsequent calls)."""
    try:
        return YOLO(model_path)
    except Exception as e:
        logger.error(f"Failed to load YOLO model: {e}")
        return None

def human_present(run_time: float = 10.0,
                  min_ratio: float = 0.3,
                  frame = None,
                  conf_thres: float = 0.4,
                  imgsz: int = 320,
                  frame_skip: int = 2) -> bool:
    print("[Human Detection] Initializing...")
    model = _load_yolo()
    if model is None:
        return False

    # if cap is None:
    #     cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    #     if not cap.isOpened():
    #         logger.error("Camera error: cannot open webcam.")
    #         return False
    #     own_cap = True
    # else:
    #     own_cap = False

    processed = 0
    positives = 0
    frame_id = 0
    start = time.time()

    try:
        while time.time() - start < run_time:
            # ret, frame = cap.read()
            # if not ret:
            #     time.sleep(0.01)
            #     continue

            frame_id += 1
            if frame_id % frame_skip != 0:
                continue

            processed += 1
            try:
                results = model(frame, classes=[0], conf=conf_thres, imgsz=imgsz, verbose=False)
                found = any(r.boxes is not None and len(r.boxes) > 0 for r in results)
                if found:
                    positives += 1
            except Exception as e:
                logger.warning(f"YOLO inference error: {e}")
    
    except Exception as e:
        logger.error(f"Error during human detection: {e}")
        return False

    ratio = (positives / processed) if processed > 0 else 0.0
    logger.info(f"[human_present] processed={processed}, positives={positives}, ratio={ratio:.2f}")
    return ratio >= min_ratio
