from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import win32api
import win32con
import time

def send_notification(title, message):
    win32api.MessageBox(0, message, title, win32con.MB_ICONINFORMATION)

def execute_task(recommendation):
    def launch_browser(url):
        try:
            options = Options()
            options.add_argument("--start-maximized")
            driver = webdriver.Chrome(options=options)
            driver.get(url)
        except Exception as e:
            print(f"Error launching browser: {e}")

    actions = {
        "Play music": lambda: launch_browser("https://open.spotify.com"),
        "Watch funny videos": lambda: launch_browser("https://www.youtube.com/results?search_query=funny+videos"),
        "Take a break": lambda: send_notification("Break Time", "Try deep breathing:\n1. Inhale 4s\n2. Hold 4s\n3. Exhale 6s"),
        "Quick game": lambda: launch_browser("https://www.chess.com/play/computer"),
        "Coding Bot": lambda: launch_browser("https://www.replit.com"),
    }

    action = actions.get(recommendation, lambda: None)
    action()

    time.sleep(5)