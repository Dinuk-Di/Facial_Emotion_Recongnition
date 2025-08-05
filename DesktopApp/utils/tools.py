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

def open_recommendations(chosen_recommendation: dict) -> bool:
    """
    Launches a local app or opens a web app (Selenium-based browser if available).
    Sends a "Time to get back to work" toast and auto-closes after 10 seconds.
    """
    app_name = chosen_recommendation.get("app_name", "Unknown App")
    app_url = chosen_recommendation.get("app_url", "")
    search_query = chosen_recommendation.get("search_query", "")
    is_local = chosen_recommendation.get("is_local", False)

    # def build_url(app_name, app_url, search_query):
    #     if search_query:
    #         encoded_query = urllib.parse.quote(search_query.strip())
    #         if app_name in SEARCH_PATTERNS:
    #             return SEARCH_PATTERNS[app_name].format(query=encoded_query)
    #         else:
    #             return f"{app_url}/results?search_query={encoded_query}"
    #     return app_url

    def build_url(app_url: str, search_query: str) -> str:
        """
        Build the full URL based on app_url and optional search_query.
        If app_url contains '<search_query>', it will be replaced by encoded query.
        If search_query is missing, '<search_query>' will be removed.
        """
        if "<search_query>" in app_url:
            if search_query and search_query.strip():
                encoded_query = urllib.parse.quote(search_query.strip())
                app_url = app_url.replace("<search_query>", encoded_query)
                print("Changed App URL", app_url)
                return app_url
            else:
                app_url = app_url.replace("<search_query>", "")  # remove placeholder if no query
                print("Changed App URL", app_url)
                return app_url
        else:
            # If there is no placeholder, append query as ?search_query=
            if search_query and search_query.strip():
                encoded_query = urllib.parse.quote(search_query.strip())
                delimiter = "&" if "?" in app_url else "?"
                app_url = f"{app_url}{delimiter}search_query={encoded_query}"
                print("Changed App URL", app_url)
                return app_url

            print("Changed App URL", app_url)
            return app_url

    def notify_and_close_local(proc):
        """
        Sends toast then terminates the process.
        """
        try:
            icon_path = os.path.join(
                os.path.dirname(__file__), "..", "assets", "res", "Icon.ico"
            )
            icon_path = os.path.abspath(icon_path) if os.path.exists(icon_path) else None
            toast = Notification(
                app_id="EMOFI",  # This replaces "Python" in the header
                title="Focus Reminder",
                msg="Time to get back to work!",
                icon= icon_path
            )
            toast.show()
        except Exception as ntf_err:
            print(f"[Toast failed] {ntf_err}")
        # give user a moment to see it
        time.sleep(0.5)
        try:
            # terminate(), fallback to kill if needed
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            proc.kill()

    def notify_and_close_driver(driver):
        """
        Sends toast then closes the Selenium driver/browser.
        """
        try:
            icon_path = os.path.join(
                os.path.dirname(__file__), "..", "assets", "res", "Icon.ico"
            )
            icon_path = os.path.abspath(icon_path) if os.path.exists(icon_path) else None
            toast = Notification(
                app_id="EMOFI",
                title="Back to Work!",
                msg="Time to get back to work!",
                icon= icon_path
            )
            toast.show()
        except Exception as ntf_err:
            print(f"[Toast failed] {ntf_err}")
        time.sleep(0.5)
        try:
            driver.quit()
        except Exception as e:
            print(f"[Driver quit failed] {e}")
            
    def launch_and_monitor_elevated(exe_path, close_after=20):
        # Launch elevated via ShellExecuteEx
        proc_info = shell.ShellExecuteEx(
            lpVerb='runas',
            lpFile=exe_path,
            lpParameters='',
            nShow=win32con.SW_SHOWNORMAL,
            fMask=shellcon.SEE_MASK_NOCLOSEPROCESS
        )
        proc_handle = proc_info['hProcess']
        pid = None
        try:
            pid = shell.GetProcessId(proc_handle)
        except Exception:
            pid = None

        if not pid:
            print("Failed to get PID; using handle directly")
        else:
            print(f"Launched elevated process PID {pid}")

        # Schedule termination
        threading.Timer(close_after, notify_and_close_elevated, args=(pid,)).start()
        return pid

    def notify_and_close_elevated(pid):
        try:
            Notification(app_id="EMOFI", title="Back to Work!",
                        msg="Time to get back to work!").show()
        except Exception as ntf:
            print("Notification failed:", ntf)

        time.sleep(0.5)
        if pid:
            try:
                proc = psutil.Process(pid)
                for child in proc.children(recursive=True):
                    child.terminate()
                proc.terminate()
                gone, alive = psutil.wait_procs([proc] + proc.children(), timeout=2)
                for p in alive:
                    p.kill()
                print(f"Killed elevated process PID {pid}")
            except Exception as e:
                print("Error killing elevated process:", e)

    # 1) Local app path
    if is_local:
        if not app_url:
            print(f"Error: No path provided for local app '{app_name}'.")
            return False
        if not os.path.isfile(app_url):
            print(f"Error: File not found for local app '{app_name}': {app_url}")
            return False

        try:
            print(f"[Launch] {app_name} from {app_url}")
            # proc = subprocess.Popen([app_url], shell=False)
            win32api.ShellExecute(
                        0,                      # hwnd: handle to parent window (0 for no parent)
                        "open",                 # operation: "open", "print", "edit", "explore", "find"
                        app_url,         # file: The program to execute (explorer.exe for shell:Appsfolder
                        None,                   # parameters: The AUMID as a shell URI
                        None,                   # directory: default directory
                        win32con.SW_SHOWNORMAL  # show command: how the application is shown
                    )
        except Exception as ex:
            print(f"Error launching local app '{app_name}': {ex}")
            return False

        # Schedule close + notification in 10 seconds
        timer = threading.Timer(20.0, launch_and_monitor_elevated, args=(app_url,))
        timer.daemon = True
        timer.start()

        print(f"Launched local app '{app_name}'. It will close after ~20 seconds.")

        return True

    # 2) Web app
    else:
        if not app_url.startswith(("http://", "https://")):
            print(f"Error: Invalid or missing URL for web app '{app_name}': {app_url}")
            return False

        url = build_url(app_url, search_query)

        # If Selenium is available, use it to open browser so we can close
        if _SELENIUM_AVAILABLE:
            try:
                options = Options()
                options.add_argument("--start-maximized")
                # launch a separate Chrome window/process
                driver = webdriver.Chrome(options=options)
                driver.get(url)
                print(f"[Selenium Open] {app_name} at {url}")
            except Exception as ex:
                print(f"[Selenium launch failed] {ex}. Falling back to webbrowser.")
                webbrowser.open(url)
                toast("Reminder", f"Opened {app_name}; can't auto-close without Selenium.")
                return f"Opened web app '{app_name}' via default browser (no Selenium)."

            # Schedule close + notification
            timer = threading.Timer(20.0, notify_and_close_driver, args=(driver,))
            timer.daemon = True
            timer.start()

            print(f"Opened web app '{app_name}' with Selenium. It will close after ~20 seconds.")

            return True

        else:
            # No selenium installed; fallback to system default browser
            try:
                webbrowser.open(url)
                print(f"[Webbrowser Open] {app_name} at {url}")
                toast("Reminder",
                      f"Opened {app_name} via default browser; install Selenium to enable auto‑close.")
                print(f"Opened '{app_name}' via webbrowser: {url}. No auto‑close due to missing Selenium.")
                return True
            except Exception as ex:
                print(f"[Webbrowser launch failed] {ex}")
                return False
