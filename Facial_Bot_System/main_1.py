import threading
import time
from face_detection import FaceEmotionDetector
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # or 2 for per-monitor V2
except:
    pass  # Fail silently if this doesn't work

def main():
    detector = FaceEmotionDetector()

    # Run detection in a background thread
    detection_thread = threading.Thread(target=detector.run, daemon=True)
    detection_thread.start()

    try:
        # Keep main thread alive to keep the app running
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Exiting...")
        # Daemon thread will exit automatically

if __name__ == "__main__":
    main()


