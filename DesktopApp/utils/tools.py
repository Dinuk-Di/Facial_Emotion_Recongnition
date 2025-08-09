import os
import subprocess
import time
import threading
import webbrowser
from winotify import Notification, audio
import urllib
import win32api
import win32gui
import win32com.shell.shell as shell
import threading
import time
import ctypes
import win32con
from win32com.shell import shellcon
import psutil

try:
    # Selenium setup for web apps—allows controlled close
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    _SELENIUM_AVAILABLE = True
except ImportError:
    _SELENIUM_AVAILABLE = False

SEARCH_PATTERNS = {
    "youtube": "https://www.youtube.com/results?search_query={query}",
    "spotify": "https://open.spotify.com/search/{query}",
    "google": "https://www.google.com/search?q={query}"
}

def open_recommendations(chosen_recommendation: dict) -> tuple:
    """
    Launches a local app or opens a web app with auto-close after 20 seconds
    Includes notification before closing
    """
    app_name = chosen_recommendation.get("app_name", "Unknown App")
    app_url = chosen_recommendation.get("app_url", "")
    search_query = chosen_recommendation.get("search_query", "")
    is_local = chosen_recommendation.get("is_local", False)
    
    def send_reminder_notification():
        """Send reminder notification before closing"""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "res", "Icon.ico")
            icon_path = os.path.abspath(icon_path) if os.path.exists(icon_path) else None
            
            toast = Notification(
                app_id="EMOFI",
                title="Time's Up!",
                msg=f"Closing {app_name} to help you focus",
                duration="long",
                icon=icon_path
            )
            toast.add_actions(label="Got it")
            toast.show()
            print("[Notification] Sent reminder")
        except Exception as e:
            print(f"[Notification Error] {e}")

    def close_local_app(pid):
        """Helper to close local app and its children"""
        try:
            # Send reminder notification
            send_reminder_notification()
            
            # Give user a moment to see notification
            time.sleep(2)
            
            # Terminate process
            proc = psutil.Process(pid)
            for child in proc.children(recursive=True):
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            proc.kill()
            print(f"[Auto-Close] Closed local app (PID: {pid})")
        except Exception as e:
            print(f"[Auto-Close] Error closing app: {e}")

    def close_web_driver(driver):
        """Helper to close web driver"""
        try:
            # Send reminder notification
            send_reminder_notification()
            
            # Give user a moment to see notification
            time.sleep(2)
            
            # Close browser
            driver.quit()
            print("[Auto-Close] Closed web browser")
        except Exception as e:
            print(f"[Auto-Close] Error closing browser: {e}")

    def build_url(app_url: str, search_query: str) -> str:
        """Build full URL with search query"""
        if "<search_query>" in app_url:
            if search_query:
                encoded_query = urllib.parse.quote(search_query.strip())
                return app_url.replace("<search_query>", encoded_query)
            return app_url.replace("<search_query>", "")
        elif search_query:
            delimiter = "&" if "?" in app_url else "?"
            return f"{app_url}{delimiter}search_query={urllib.parse.quote(search_query.strip())}"
        return app_url

    # 1) Local app path
    if is_local:
        if not app_url or not os.path.isfile(app_url):
            print(f"Error: Invalid path for local app '{app_name}': {app_url}")
            return False, None, None

        try:
            print(f"[Launch] {app_name} from {app_url}")
            proc = subprocess.Popen([app_url])
            pid = proc.pid
            print(f"[Local App] Launched {app_name} with PID: {pid}")
            
            
            # Start auto-close timer
            threading.Timer(20.0, close_local_app, args=(pid,)).start()
            
            return True, pid, 'local'
        except Exception as ex:
            print(f"Error launching local app: {ex}")
            return False, None, None

    # 2) Web app
    else:
        if not app_url.startswith(("http://", "https://")):
            print(f"Error: Invalid URL for web app '{app_name}': {app_url}")
            return False, None, None

        url = build_url(app_url, search_query)

        # Use Selenium for web apps to enable auto-close
        if _SELENIUM_AVAILABLE:
            try:
                options = Options()
                options.add_argument("--start-maximized")
                driver = webdriver.Chrome(options=options)
                driver.get(url)
                print(f"[Selenium] Opened {app_name} at {url}")
                
                # Start auto-close timer
                threading.Timer(20.0, close_web_driver, args=(driver,)).start()
                
                return True, driver, 'web'
            except Exception as ex:
                print(f"Selenium error: {ex}")
                # Fall through to webbrowser method

        # Fallback to default browser (no auto-close)
        try:
            webbrowser.open(url)
            print(f"[Webbrowser] Opened {app_name} at {url}")
            
            # Send notification that we can't auto-close
            try:
                toast = Notification(
                    app_id="EMOFI",
                    title="No Auto-Close",
                    msg=f"Opened in default browser. Close manually when done.",
                    duration="long"
                )
                toast.show()
            except Exception:
                pass
            
            return True, None, 'web'
        except Exception as ex:
            print(f"Webbrowser error: {ex}")
            return False, None, None
            
    return False, None, None