import threading
import time
from core.human_detector import human_present
from core.sleepy_detector import check_sleepy
from core.emotion_detector import get_emotion
from core.hand_movement import detect_hand
from core.agent_system import run_agent_system

class AppController:
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_seen = time.time()
        self.agent_mode = False

    def start(self):
        self.running = True
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False

    def run(self):
        while self.running:
            if human_present():
                self.last_seen = time.time()
                # sleepy = check_sleepy()
                # if sleepy:
                #     print("[ALERT] Sleepy detected! 🔔")

                # emotion = get_emotion()
                # print(f"[INFO] Detected Emotion: {emotion}")

                # hand = detect_hand()
                # print(f"[INFO] Detected Hand Movement: {hand}")

                # human_detector = human_present()
                # print(f"[INFO] Human Detected: {human_detector}")

                sleep_detector = check_sleepy()
                print(f"[INFO] Sleepy Detected: {sleep_detector}")
                
                # avg_array = (0.3 * hand) + (0.7 * emotion)
                # print(f"[INFO] Avg Emotion: {avg_array:.2f}")

                # time.sleep(60)  # Delay before agent runs

                # self.agent_mode = True
                # run_agent_system(avg_array)
                # self.agent_mode = False

            else:
                if time.time() - self.last_seen >= 300:
                    print("[INFO] No person detected for 5 mins. Sleeping other detectors.")
                    time.sleep(5)

            time.sleep(2)
