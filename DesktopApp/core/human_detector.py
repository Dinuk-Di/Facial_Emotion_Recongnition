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
                  cam_index: int = 0,
                  conf_thres: float = 0.4,
                  imgsz: int = 320,
                  frame_skip: int = 2) -> bool:
    """
    Check for `run_time` seconds whether a human (class 0) appears in frames.
    We process every `frame_skip`-th frame to reduce compute and average the
    detections. If (positives / processed) >= min_ratio -> return True else False.

    Args:
        run_time   : seconds to observe
        min_ratio  : minimum fraction of processed frames that must contain a person
        cam_index  : webcam index
        conf_thres : YOLO confidence threshold
        imgsz      : YOLO inference size (smaller = faster)
        frame_skip : only run YOLO on every Nth frame

    Returns:
        bool: True if human present often enough, else False
    """
    model = _load_yolo()
    if model is None:
        return False

    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        logger.error("Camera error: cannot open webcam.")
        return False

    processed = 0
    positives = 0
    frame_id = 0
    start = time.time()

    try:
        while time.time() - start < run_time:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            frame_id += 1
            if frame_id % frame_skip != 0:
                continue  # skip to save CPU

            processed += 1

            # Optional downscale before sending to YOLO (ultralytics can also handle imgsz)
            # but we still pass imgsz for internal resizing.
            try:
                results = model(
                    frame,
                    classes=[0],          # 0 = person
                    conf=conf_thres,
                    imgsz=imgsz,
                    verbose=False
                )
                # Positive if any detection exists
                found = any(r.boxes is not None and len(r.boxes) > 0 for r in results)
                if found:
                    positives += 1
            except Exception as e:
                logger.warning(f"YOLO inference error: {e}")

    finally:
        cap.release()

    ratio = (positives / processed) if processed > 0 else 0.0
    logger.info(f"[human_present] processed={processed}, positives={positives}, ratio={ratio:.2f}")

    return ratio >= min_ratio
