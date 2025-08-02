#recomender tools
import os
import subprocess
import webbrowser
import win32api # New import
import win32con # New import
import psutil
import time
import winapps
from dotenv import load_dotenv
from typing import Optional,Dict, List
import webbrowser
from utils.runner_contactsWidget import ContactWindow
import uuid
from PySide6.QtWidgets import QApplication, QMessageBox
from app_config import kNOWN_APPS_LIST
from communication_apps_config import COMMUNICATION_APPS_LIST
import json
import sqlite3
from datetime import datetime, timedelta
import os
from pathlib import Path
import re
from telethon.sync import TelegramClient
from telethon.tl import functions  # Add this with other imports
from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.functions.messages import GetHistoryRequest
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.notifications import send_notification

import time
import threading

launched_apps = {}
opened_browser_instances = []  # Track browser instances we launched
opened_browser_tabs: List[Dict] = []  # Track individual tabs
# Store opened apps info with timestamps
opened_apps_info = []  # Each item: dict with keys: type='desktop'|'web', process=psutil.Process, opened_at=timestamp, driver=webdriver (optional)

# Timeout duration in seconds (15 minutes)
APP_TIMEOUT_SECONDS = 30
APP_WARNING_SECONDS = 20


def get_browser_path(browser_name: str) -> Optional[str]:
    """Get the path to the browser executable based on name"""
    browser_name = browser_name.lower()
    paths = {
        'chrome': r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        'msedge': r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        'firefox': r"C:\Program Files\Mozilla Firefox\firefox.exe",
        'opera': r"C:\Program Files\Opera\launcher.exe"
    }
    
    for name, path in paths.items():
        if browser_name in name:
            if os.path.exists(path):
                return path
    return None

def is_app_installed(app_name: str) -> bool:
    app_name = app_name.lower()
    if app_name in COMMUNICATION_APPS_LIST:
        process_name = COMMUNICATION_APPS_LIST[app_name]["process"]
        if any(proc.info['name'].lower() == process_name.lower() 
               for proc in psutil.process_iter(['name'])):
            return True
        
        try:
            return any(app_name in app.name.lower() 
                       for app in winapps.list_installed())
        except ImportError:
            print("winapps not available, limited installation detection")
    
    return False

def open_recommendation(recommendation: dict) -> str:

    global launched_apps, opened_browser_tabs, opened_apps_info

    print(f"[Open_recommendation] {recommendation}")
    url = recommendation.get("app_url", "")
    app_name = recommendation.get("app_name", "")
    app_name_lower = app_name.lower()

    for app_info in kNOWN_APPS_LIST:
        # Check for a match (case-insensitive, allows partial for longer names)
        if app_name_lower == app_info["name"].lower() or \
           (app_name_lower in app_info["name"].lower() and len(app_name_lower) > 2):

            # Desktop app launch path
            process = None
            if "aumid" in app_info and app_info["aumid"]:
                aumid_to_use = app_info["aumid"]
                try:
                    win32api.ShellExecute(
                        0,                      # hwnd: handle to parent window (0 for no parent)
                        "open",                 # operation: "open", "print", "edit", "explore", "find"
                        "explorer.exe",         # file: The program to execute (explorer.exe for shell:Appsfolder)
                        aumid_to_use,           # parameters: The AUMID as a shell URI
                        None,                   # directory: default directory
                        win32con.SW_SHOWNORMAL  # show command: how the application is shown
                    )

                    time.sleep(2)  # Give app time to launch
                    processes = []
                    for proc in psutil.process_iter(['name']):
                        if proc.info['name'].lower() == app_info["process"].lower():
                            processes.append(proc)

                    if processes:
                        opened_apps_info.append({
                            'type': 'desktop',
                            'processes': processes,
                            'app_name': app_info["name"],
                            'opened_at': time.time()
                        })
                        print("opened app info aumid process: ", opened_apps_info)
                    start_monitoring_thread()
                    return f"Successfully launched {app_info['name']} via AUMID: '{aumid_to_use}'."
                except Exception as e:
                    return f"Error launching {app_info['name']} via AUMID '{aumid_to_use}': {e}"
            elif "location" in app_info and app_info["location"]:    
                app_path_to_use = app_info["location"]

                if not app_path_to_use:
                    return f"Error: No path provided for {app_info['name']} in the list."

                # Attempt to launch the app using the provided path
                try:
                    win32api.ShellExecute(
                        0,                           # hwnd
                        "open",                      # operation
                        app_path_to_use,             # file: the path to the executable or shortcut
                        None,                        # parameters (not needed for simple open)
                        None,                        # directory
                        win32con.SW_SHOWNORMAL       # show command
                    )
                    
                    time.sleep(2)  # Give app time to launch
                    matching_procs = []
                    for proc in psutil.process_iter(['name']):
                        try:
                            if proc.info['name'].lower() == app_info["process"].lower():
                                matching_procs.append(proc)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue

                    if matching_procs:
                        # Save the list of processes instead of single process
                        opened_apps_info.append({
                            'type': 'desktop',
                            'processes': matching_procs,
                            'app_name': app_info["name"],
                            'opened_at': time.time()
                        })
                        print("opened_app_info : ",opened_apps_info)
                    start_monitoring_thread()
                    return f"Successfully launched {app_info['name']} using path: {app_path_to_use}."
                except Exception as e:
                    return f"Error launching {app_info['name']} from {app_path_to_use}: {e}"
            else:
                return f"Error: No valid launch method (location or aumid) provided for '{app_info['name']}' in the 'known_apps_list'."
    if url.startswith(("http://", "https://")):
        try:
            # Add search query if present
            if recommendation.get("search_query"):
                search = recommendation["search_query"].replace(" ", "+")
                url += f"/results?search_query={search}"
            # Open new Selenium browser window each time
            print("Web URL: ", url)
            options = webdriver.ChromeOptions()
            options.add_argument("--new-window")  # Open in new window
            driver = webdriver.Chrome(options=options)
            driver.get(url)


            opened_browser_tabs.append({
                'url': url,
                'browser': 'chrome',
                'method': 'selenium',
                'driver': driver,
                'window_handle': driver.current_window_handle,
                'opened_at': time.time()
            })

            opened_apps_info.append({
                'type': 'web',
                'driver': driver,
                'url': url,
                'opened_at': time.time()
            })
            print("opened app info: ", opened_apps_info)
            start_monitoring_thread()
            return f"Opened {url} in default browser tab."
        except Exception as selenium_error:
            webbrowser.open(url)
            return f"Failed to open URL '{url}': {e}"

    return f"Recommendation '{recommendation}' is neither a recognized URL nor a known application."
    
def terminate_process_tree(proc):
    try:
        children = proc.children(recursive=True)
        for child in children:
            try:
                child.terminate()
            except Exception:
                pass
        proc.terminate()
        gone, alive = psutil.wait_procs([proc] + children, timeout=5)
        for p in alive:
            try:
                p.kill()
            except Exception:
                pass
    except Exception as e:
        print(f"Error terminating process tree: {e}")

def close_tracked_app(app_info):
    try:
        if app_info['type'] == 'desktop':
            for proc in app_info.get('processes', []):
              terminate_process_tree(proc)
            print(f"Closed desktop app: {app_info.get('app_name')}")
        elif app_info['type'] == 'web':
            driver = app_info.get('driver')
            if driver:
                driver.quit()
                return True 
            print(f"Closed browser window for URL: {app_info.get('url')}")
    except Exception as e:
        print(f"Error closing app: {e}")

def monitor_opened_apps():
    current_time = time.time()
    to_remove = []
    is_closed = False
    closing_text = "Time to get back to work"
    
    for app_info in opened_apps_info:
        if abs((current_time - app_info['opened_at']) - APP_WARNING_SECONDS) <= 1: 
            user_action = send_notification(closing_text)
            if user_action:
                is_closed = close_tracked_app(app_info)
                to_remove.append(app_info)
        elif current_time - app_info['opened_at'] >= APP_TIMEOUT_SECONDS:
            is_closed = close_tracked_app(app_info)
            to_remove.append(app_info)
        
    for app_info in to_remove:
        opened_apps_info.remove(app_info)
    return is_closed

def start_monitoring_thread(interval_sec=60):
    def monitor_loop():
        app_is_closed = False
        while not app_is_closed:
            app_is_closed = monitor_opened_apps()
    print("start monitoring")
    thread = threading.Thread(target=monitor_loop, daemon=False)
    thread.start()
    print("opened app info: ", opened_apps_info)


def format_timestamp(timestamp):
    """Convert various timestamp formats to human-readable"""
    try:
        if timestamp > 1e12:  # WhatsApp timestamp (microseconds)
            dt = datetime.fromtimestamp(timestamp/1000)
        elif timestamp > 1e9:  # Unix timestamp
            dt = datetime.fromtimestamp(timestamp)
        else:  # Teams timestamp (milliseconds)
            dt = datetime.fromtimestamp(timestamp/1000)
            
        if dt.date() == datetime.today().date():
            return dt.strftime("%H:%M")
        elif dt.date() == (datetime.today() - timedelta(days=1)).date():
            return "Yesterday"
        else:
            return dt.strftime("%Y-%m-%d")
    except:
        return "Recently"
    
# import os
# import subprocess
# import webbrowser
# import win32api # New import
# import win32con # New import
# import psutil
# import time
# import winapps
# from dotenv import load_dotenv
# from typing import Optional,Dict, List
# import webbrowser
# from utils.runner_contactsWidget import ContactWindow
# import uuid
# from PySide6.QtWidgets import QApplication, QMessageBox
# from app_config import kNOWN_APPS_LIST
# from communication_apps_config import COMMUNICATION_APPS_LIST
# import json
# import sqlite3
# from datetime import datetime, timedelta
# import os
# from pathlib import Path
# import re
# from telethon.sync import TelegramClient
# from telethon.tl import functions  # Add this with other imports
# from telethon.tl.functions.contacts import GetContactsRequest
# from telethon.tl.functions.messages import GetHistoryRequest
# import asyncio
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from utils.notifications import send_notification
# import pywhatkit

# import time
# import threading

# launched_apps = {}
# opened_browser_instances = []  # Track browser instances we launched
# opened_browser_tabs: List[Dict] = []  # Track individual tabs
# # Store opened apps info with timestamps
# opened_apps_info = []  # Each item: dict with keys: type='desktop'|'web', process=psutil.Process, opened_at=timestamp, driver=webdriver (optional)

# # Timeout duration in seconds (15 minutes)
# APP_TIMEOUT_SECONDS = 30
# APP_WARNING_SECONDS = 20


# def get_browser_path(browser_name: str) -> Optional[str]:
#     """Get the path to the browser executable based on name"""
#     browser_name = browser_name.lower()
#     paths = {
#         'chrome': r"C:\Program Files\Google\Chrome\Application\chrome.exe",
#         'msedge': r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
#         'firefox': r"C:\Program Files\Mozilla Firefox\firefox.exe",
#         'opera': r"C:\Program Files\Opera\launcher.exe"
#     }
    
#     for name, path in paths.items():
#         if browser_name in name:
#             if os.path.exists(path):
#                 return path
#     return None

# def is_app_installed(app_name: str) -> bool:
#     app_name = app_name.lower()
#     if app_name in COMMUNICATION_APPS_LIST:
#         process_name = COMMUNICATION_APPS_LIST[app_name]["process"]
#         if any(proc.info['name'].lower() == process_name.lower() 
#                for proc in psutil.process_iter(['name'])):
#             return True
        
#         try:
#             return any(app_name in app.name.lower() 
#                        for app in winapps.list_installed())
#         except ImportError:
#             print("winapps not available, limited installation detection")
    
#     return False

# def open_recommendation(recommendation: dict) -> str:

#     global launched_apps, opened_browser_tabs, opened_apps_info

#     print(f"[Open_recommendation] {recommendation}")
#     url = recommendation.get("app_url", "")
#     app_name = recommendation.get("app_name", "")
#     app_name_lower = app_name.lower()

#     # Handle WhatsApp specially
#     if app_name_lower == "whatsapp":
#         action = recommendation.get("action", "open_app")
#         if action == "send_message":
#             try:
#                 phone_number = recommendation["phone_number"]
#                 message = recommendation.get("message", "")
#                 # Fallback to pywhatkit
#                 pywhatkit.sendwhatmsg_instantly(
#                     phone_no=phone_number,
#                     message=message,
#                     wait_time=15,
#                     tab_close=True,
#                     close_time=3
#                 )
#                 return f"Sent WhatsApp message to {phone_number}"
#             except Exception as e:
#                 return f"Failed to send WhatsApp message: {e}"

#     for app_info in kNOWN_APPS_LIST:
#         # Check for a match (case-insensitive, allows partial for longer names)
#         if app_name_lower == app_info["name"].lower() or \
#            (app_name_lower in app_info["name"].lower() and len(app_name_lower) > 2):

#             # Desktop app launch path
#             process = None
#             if "aumid" in app_info and app_info["aumid"]:
#                 aumid_to_use = app_info["aumid"]
#                 try:
#                     win32api.ShellExecute(
#                         0,                      # hwnd: handle to parent window (0 for no parent)
#                         "open",                 # operation: "open", "print", "edit", "explore", "find"
#                         "explorer.exe",         # file: The program to execute (explorer.exe for shell:Appsfolder)
#                         aumid_to_use,           # parameters: The AUMID as a shell URI
#                         None,                   # directory: default directory
#                         win32con.SW_SHOWNORMAL  # show command: how the application is shown
#                     )

#                     time.sleep(2)  # Give app time to launch
#                     processes = []
#                     for proc in psutil.process_iter(['name']):
#                         if proc.info['name'].lower() == app_info["process"].lower():
#                             processes.append(proc)

#                     if processes:
#                         opened_apps_info.append({
#                             'type': 'desktop',
#                             'processes': processes,
#                             'app_name': app_info["name"],
#                             'opened_at': time.time()
#                         })
#                         print("opened app info aumid process: ", opened_apps_info)
#                     start_monitoring_thread()
#                     return f"Successfully launched {app_info['name']} via AUMID: '{aumid_to_use}'."
#                 except Exception as e:
#                     return f"Error launching {app_info['name']} via AUMID '{aumid_to_use}': {e}"
#             elif "location" in app_info and app_info["location"]:    
#                 app_path_to_use = app_info["location"]

#                 if not app_path_to_use:
#                     return f"Error: No path provided for {app_info['name']} in the list."

#                 # Attempt to launch the app using the provided path
#                 try:
#                     win32api.ShellExecute(
#                         0,                           # hwnd
#                         "open",                      # operation
#                         app_path_to_use,             # file: the path to the executable or shortcut
#                         None,                        # parameters (not needed for simple open)
#                         None,                        # directory
#                         win32con.SW_SHOWNORMAL       # show command
#                     )
                    
#                     time.sleep(2)  # Give app time to launch
#                     matching_procs = []
#                     for proc in psutil.process_iter(['name']):
#                         try:
#                             if proc.info['name'].lower() == app_info["process"].lower():
#                                 matching_procs.append(proc)
#                         except (psutil.NoSuchProcess, psutil.AccessDenied):
#                             continue

#                     if matching_procs:
#                         # Save the list of processes instead of single process
#                         opened_apps_info.append({
#                             'type': 'desktop',
#                             'processes': matching_procs,
#                             'app_name': app_info["name"],
#                             'opened_at': time.time()
#                         })
#                         print("opened_app_info : ",opened_apps_info)
#                     start_monitoring_thread()
#                     return f"Successfully launched {app_info['name']} using path: {app_path_to_use}."
#                 except Exception as e:
#                     return f"Error launching {app_info['name']} from {app_path_to_use}: {e}"
#             else:
#                 return f"Error: No valid launch method (location or aumid) provided for '{app_info['name']}' in the 'known_apps_list'."
#     if url.startswith(("http://", "https://")):
#         try:
#             # Add search query if present
#             if recommendation.get("search_query"):
#                 search = recommendation["search_query"].replace(" ", "+")
#                 url += f"/results?search_query={search}"
#             # Open new Selenium browser window each time
#             print("Web URL: ", url)
#             options = webdriver.ChromeOptions()
#             options.add_argument("--new-window")  # Open in new window
#             driver = webdriver.Chrome(options=options)
#             driver.get(url)


#             opened_browser_tabs.append({
#                 'url': url,
#                 'browser': 'chrome',
#                 'method': 'selenium',
#                 'driver': driver,
#                 'window_handle': driver.current_window_handle,
#                 'opened_at': time.time()
#             })

#             opened_apps_info.append({
#                 'type': 'web',
#                 'driver': driver,
#                 'url': url,
#                 'opened_at': time.time()
#             })
#             print("opened app info: ", opened_apps_info)
#             start_monitoring_thread()
#             return f"Opened {url} in default browser tab."
#         except Exception as selenium_error:
#             webbrowser.open(url)
#             return f"Failed to open URL '{url}': {e}"

#     return f"Recommendation '{recommendation}' is neither a recognized URL nor a known application."
    
# def terminate_process_tree(proc):
#     try:
#         children = proc.children(recursive=True)
#         for child in children:
#             try:
#                 child.terminate()
#             except Exception:
#                 pass
#         proc.terminate()
#         gone, alive = psutil.wait_procs([proc] + children, timeout=5)
#         for p in alive:
#             try:
#                 p.kill()
#             except Exception:
#                 pass
#     except Exception as e:
#         print(f"Error terminating process tree: {e}")

# def close_tracked_app(app_info):
#     try:
#         if app_info['type'] == 'desktop':
#             for proc in app_info.get('processes', []):
#               terminate_process_tree(proc)
#             print(f"Closed desktop app: {app_info.get('app_name')}")
#         elif app_info['type'] == 'web':
#             driver = app_info.get('driver')
#             if driver:
#                 driver.quit()
#                 return True 
#             print(f"Closed browser window for URL: {app_info.get('url')}")
#     except Exception as e:
#         print(f"Error closing app: {e}")

# def monitor_opened_apps():
#     current_time = time.time()
#     to_remove = []
#     is_closed = False
#     closing_text = "Time to get back to work"
    
#     for app_info in opened_apps_info:
#         if abs((current_time - app_info['opened_at']) - APP_WARNING_SECONDS) <= 1: 
#             user_action = send_notification(closing_text)
#             if user_action:
#                 is_closed = close_tracked_app(app_info)
#                 to_remove.append(app_info)
#         elif current_time - app_info['opened_at'] >= APP_TIMEOUT_SECONDS:
#             is_closed = close_tracked_app(app_info)
#             to_remove.append(app_info)
        
#     for app_info in to_remove:
#         opened_apps_info.remove(app_info)
#     return is_closed

# def start_monitoring_thread(interval_sec=60):
#     def monitor_loop():
#         app_is_closed = False
#         while not app_is_closed:
#             app_is_closed = monitor_opened_apps()
#     print("start monitoring")
#     thread = threading.Thread(target=monitor_loop, daemon=False)
#     thread.start()
#     print("opened app info: ", opened_apps_info)


# def format_timestamp(timestamp):
#     """Convert various timestamp formats to human-readable"""
#     try:
#         if timestamp > 1e12:  # WhatsApp timestamp (microseconds)
#             dt = datetime.fromtimestamp(timestamp/1000)
#         elif timestamp > 1e9:  # Unix timestamp
#             dt = datetime.fromtimestamp(timestamp)
#         else:  # Teams timestamp (milliseconds)
#             dt = datetime.fromtimestamp(timestamp/1000)
            
#         if dt.date() == datetime.today().date():
#             return dt.strftime("%H:%M")
#         elif dt.date() == (datetime.today() - timedelta(days=1)).date():
#             return "Yesterday"
#         else:
#             return dt.strftime("%Y-%m-%d")
#     except:
#         return "Recently"

    

#runner_interface
import ctypes
import sys
from utils.mainWindowInterface import InteraceMainwindow
import os
import sys
import re
import time
import win32api
import win32con
import pywhatkit
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import Qt, QFile, QTextStream
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

Icons_paths = [
        {"app_name": "YouTube","icon_path": "utils/res/Youtube.png"},
        {"app_name": "Spotify","icon_path": "utils/res/Spotify.png"},
        {"app_name": "Discord","icon_path": "utils/res/Discord.png"},
        {"app_name": "Zoom","icon_path": "utils/res/Zoom.png"},
        {"app_name": "Microsoft Teams","icon_path": "utils/res/Teams.png"},
        {"app_name": "Skype","icon_path": "utils/res/Skype.png"},
        {"app_name": "Telegram Desktop","icon_path": "utils/res/Telegram.png"},
        {"app_name": "WhatsApp","icon_path": "utils/res/Whatsapp.png"},
        {"app_name": "Microsoft Solitaire Collection","icon_path": "utils/res/Solitaire.png"},
        {"app_name": "Default","icon_path": "utils/res/default_app.png"},
    ]

def setup_Icons(app_name, icon_paths):
    default_icon = "utils/res/default_app.png"
    icon_path = default_icon
    
    for idx, icon in enumerate(icon_paths):
        if app_name == icon['app_name']:
            icon_path = icon['icon_path']
            break
    return icon_path

class MainWindow(QMainWindow):
    def __init__(self, choices):
        super().__init__()
        # Configure DPI awareness before UI setup
        self.configure_dpi_awareness()

        self.selectedChoice = None
        self.allchoices = choices
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.ui = InteraceMainwindow()
        self.ui.setupUi(self)

        # Configure ChromeDriver
        self.chrome_service = self.setup_chrome_service()

        # Connect search callback
        self.ui.search_callback = self.handle_youtube_search
        self.ui.telegram_search_callback = self.handle_telegram_search
        self.ui.whatsapp_callback = self.handle_whatsapp_message
        self.move(990, 580)

        for idx, choice in enumerate(choices[0:2]):
            icon = setup_Icons(choice['app_name'], Icons_paths)
            self.add_choice_main(choice['text'], idx, icon, self.on_clicked_choice)
        self.ui.Close_Btn.clicked.connect(self.close)

    def add_choice_main(self, text, id=None, icon_path= None, on_click = None):
        self.ui.add_choice(text, id, icon_path, on_click)

    def on_clicked_choice(self, content, id):
        selected = self.allchoices[id]
        self.selectedChoice = selected
        self.ui.selected_choice = selected  # Store for default query
        
        if selected.get('app_name', '').lower() == 'youtube':
            self.ui.show_search()
            self.ui.search_input.setFocus()
            default_query = selected.get('search_query', '')
            self.ui.search_input.setPlaceholderText(f"e.g. {default_query}" if default_query else "Enter search query...")
        # elif selected.get('app_name', '').lower() == 'telegram desktop':
        #     self.ui.show_search("telegram")
        #     self.ui.search_input.setFocus()
        #     self.ui.search_input.setPlaceholderText("Enter Telegram username (e.g., @username)")
        elif selected.get('app_name', '').lower() == 'whatsapp':
            self.ui.show_search("whatsapp")
            self.ui.search_input.setFocus()
            self.ui.search_input.setPlaceholderText("Enter phone number (e.g., +1234567890)")
        else:
            print(f"Selected: {id},{content}")
            self.close()

    
    def handle_youtube_search(self, query):
        if query is None:  # User cancelled
            return
            
        # Find the YouTube option
        youtube_choice = None
        for choice in self.allchoices:
            if choice.get('app_name', '').lower() == 'youtube':
                youtube_choice = choice
                break
                
        if youtube_choice:
            # Update the choice with the custom query
            youtube_choice['search_query'] = query
            self.selectedChoice = youtube_choice
            self.close()
    #def show_recommendations(self, show):

    def handle_telegram_search(self, username):
        if not username or not username.strip():
            QMessageBox.warning(self, "Input Error", "Please enter a Telegram username")
            return
        
        username = username.lstrip('@')

         # Show processing dialog
        progress = QMessageBox(self)
        progress.setWindowTitle("Searching")
        progress.setText(f"Searching for @{username}...")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.show()
        QApplication.processEvents()
        
        try:
            user_id = self.get_telegram_user_id(username)
            if user_id:
                # Process successful result
                telegram_choice = next(
                    (c for c in self.allchoices 
                    if c.get('app_name', '').lower() == 'telegram desktop'),
                    None
                )
                if telegram_choice:
                    telegram_choice.update({
                        'telegram_user_id': user_id,
                        'telegram_username': f"@{username}",
                        'app_url': f"https://t.me/{username}"
                    })
                    self.selectedChoice = telegram_choice
        except Exception as e:
            QMessageBox.critical(self, "Search Error", f"Failed to search user: {str(e)}")
        finally:
            progress.close()
            self.close()

    def handle_whatsapp_message(self, phone_number, message):
        if not phone_number or not phone_number.strip():
            QMessageBox.warning(self, "Input Error", "Please enter a phone number")
            return
            
        # Clean and validate phone number format
        phone_number = phone_number.strip()
        if not phone_number.startswith('+94'):
            phone_number = '+94' + phone_number.lstrip('+')
        
        if not re.match(r'^\+94[0-9]{9}$', phone_number):
            QMessageBox.warning(self, "Input Error", 
                "Please enter a valid Sri Lankan phone number (e.g., +94771234567)")
            return

            
        if not message or not message.strip():
            QMessageBox.warning(self, "Input Error", "Please enter a message")
            return
        # Show processing dialog
        progress = QMessageBox(self)
        progress.setWindowTitle("Sending")
        progress.setText(f"Sending message to {phone_number}...")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.show()
        QApplication.processEvents()
        try:
            # Find the WhatsApp option
            whatsapp_choice = next(
                (c for c in self.allchoices 
                if c.get('app_name', '').lower() == 'whatsapp'),
                None
            )
            if whatsapp_choice:
                whatsapp_choice.update({
                    'phone_number': phone_number.strip(),
                    'message': message.strip()
                })
                self.selectedChoice = whatsapp_choice
                
                # Send the message using pywhatkit
                pywhatkit.sendwhatmsg_instantly(
                    phone_no=phone_number.strip(),
                    message=message.strip(),
                    wait_time=15,
                    tab_close=True,
                    close_time=3
                )
        except Exception as e:
            QMessageBox.critical(self, "Send Error", f"Failed to send message: {str(e)}")
        finally:
            progress.close()
            self.close()


    def configure_dpi_awareness(self):
        """Multi-layered DPI awareness configuration"""
        try:
            # Windows API level (works on Windows 10 1607+)
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
        except:
            try:
                # Fallback for older Windows versions
                ctypes.windll.user32.SetProcessDPIAware()
            except:
                pass
        
        # Qt level
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        os.environ["QT_SCALE_FACTOR"] = "1"
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    def setup_chrome_service(self):
        """Robust ChromeDriver setup with multiple fallbacks"""
        try:
            # Method 1: Automatic management with proper ChromeType detection
            driver_path = ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install()
            service = Service(driver_path)
            # Test the driver
            options = Options()
            options.add_argument("--headless")
            test_driver = webdriver.Chrome(service=service, options=options)
            test_driver.quit()
            return service
        except Exception as e:
            print(f"ChromeDriver auto-install failed: {e}")
            
            # # Method 2: Try common paths
            # common_paths = [
            #     "chromedriver.exe",
            #     os.path.join(os.getenv("ProgramFiles"), "Google", "Chrome", "Application", "chromedriver.exe"),
            #     os.path.join(os.getenv("ProgramFiles(x86)"), "Google", "Chrome", "Application", "chromedriver.exe")
            # ]
            
            # for path in common_paths:
            #     if os.path.exists(path):
            #         try:
            #             service = Service(path)
            #             # Test the driver
            #             options = Options()
            #             options.add_argument("--headless")
            #             test_driver = webdriver.Chrome(service=service, options=options)
            #             test_driver.quit()
            #             return service
            #         except Exception as e:
            #             print(f"ChromeDriver at {path} failed: {e}")
            #             continue
            
            # # Method 3: Try system PATH
            # try:
            #     service = Service()
            #     options = Options()
            #     options.add_argument("--headless")
            #     test_driver = webdriver.Chrome(service=service, options=options)
            #     test_driver.quit()
            #     return service
            # except:
            #     QMessageBox.critical(None, "ChromeDriver Error",
            #         "Could not initialize ChromeDriver.\n\n"
            #         "Please ensure:\n"
            #         "1. Chrome is installed from https://www.google.com/chrome/\n"
            #         "2. Matching ChromeDriver is downloaded from https://chromedriver.chromium.org/\n"
            #         "3. ChromeDriver is placed in your project folder or system PATH")
            #     return None

    def get_telegram_user_id(self, username):
        """Robust Telegram user ID extraction"""
        if not self.chrome_service:
            return None

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1280,720")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = None

        try:
            driver = webdriver.Chrome(service=self.chrome_service, options=options)
            driver.get("https://web.telegram.org/")
            
            # Show persistent dialog until user confirms scan
            msg = QMessageBox(self)
            msg.setWindowTitle("Telegram Login Required")
            msg.setText("Please:\n1. Scan the QR code in the browser window\n2. Click OK when logged in")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
            
            # Search for user
            search_box = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Search"]'))
            )
            search_box.clear()
            search_box.send_keys(username)
            
            # Wait for and click user
            user_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f'//div[contains(@class, "ChatInfo") and contains(., "{username}")]'))
            )
            user_element.click()
            
            # Extract ID from URL
            WebDriverWait(driver, 10).until(
                lambda d: "#" in d.current_url
            )
            return driver.current_url.split("#")[-1]
            
        except Exception as e:
            QMessageBox.warning(self, "Search Error", 
                f"Failed to find Telegram user:\n{str(e)}\n\n"
                "Please ensure:\n"
                "1. You're logged in to Telegram Web\n"
                "2. The username exists in your contacts")
            return None
        finally:
            if driver:
                driver.quit()

def launch_window(options):
    # Enable High-DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    """Function to create and return the window instance"""
    # app = QApplication.instance()
    # if not app:
    #     app = QApplication(sys.argv)
    #     # Apply style sheet if needed
    #     style_file = QFile("style.qss")
    #     if style_file.open(QFile.ReadOnly | QFile.Text):
    #         stream = QTextStream(style_file)
    #         app.setStyleSheet(stream.readAll())

    # Create application instance
    app = QApplication(sys.argv)
    
    # Apply styles if available
    if os.path.exists("style.qss"):
        with open("style.qss", "r") as f:
            app.setStyleSheet(f.read())
    
    # Create and show main window
    # window = MainWindow(options)
    # window.show()

    
    window = MainWindow(choices=options)
    window.show()
    # Debug output
    print("Application and window initialized:")
    print(f"App: {app}")
    print(f"Window: {window}")
    return window, app

if __name__ == "__main__":
    app = QApplication(sys.argv)

    options = [
        {'text': 'Watch relaxing video'},
        {'text': 'Watch funny video'}
    ]
    
    window = MainWindow(options)
    window.show()
    app.exec()
    print("Final choice: ", window.selectedChoice)


    
# import ctypes
# import sys
# from utils.mainWindowInterface import InteraceMainwindow
# import os
# import sys
# import re
# import time
# import win32api
# import win32con
# import pywhatkit
# from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
# from PySide6.QtCore import Qt, QFile, QTextStream
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager
# from webdriver_manager.core.os_manager import ChromeType

# Icons_paths = [
#         {"app_name": "YouTube","icon_path": "utils/res/Youtube.png"},
#         {"app_name": "Spotify","icon_path": "utils/res/Spotify.png"},
#         {"app_name": "Discord","icon_path": "utils/res/Discord.png"},
#         {"app_name": "Zoom","icon_path": "utils/res/Zoom.png"},
#         {"app_name": "Microsoft Teams","icon_path": "utils/res/Teams.png"},
#         {"app_name": "Skype","icon_path": "utils/res/Skype.png"},
#         {"app_name": "Telegram Desktop","icon_path": "utils/res/Telegram.png"},
#         {"app_name": "WhatsApp","icon_path": "utils/res/Whatsapp.png"},
#         {"app_name": "Microsoft Solitaire Collection","icon_path": "utils/res/Solitaire.png"},
#         {"app_name": "Default","icon_path": "utils/res/default_app.png"},
#     ]

# def setup_Icons(app_name, icon_paths):
#     default_icon = "utils/res/default_app.png"
#     icon_path = default_icon
    
#     for idx, icon in enumerate(icon_paths):
#         if app_name == icon['app_name']:
#             icon_path = icon['icon_path']
#             break
#     return icon_path

# class MainWindow(QMainWindow):
#     def __init__(self, choices):
#         super().__init__()
#         # Configure DPI awareness before UI setup
#         self.configure_dpi_awareness()

#         self.selectedChoice = None
#         self.allchoices = choices
#         self.setWindowFlag(Qt.FramelessWindowHint)
#         self.setAttribute(Qt.WA_TranslucentBackground)
#         self.ui = InteraceMainwindow()
#         self.ui.setupUi(self)

#         # Configure ChromeDriver
#         self.chrome_service = self.setup_chrome_service()

#         # Connect search callback
#         self.ui.search_callback = self.handle_youtube_search
#         self.ui.telegram_search_callback = self.handle_telegram_search
#         self.ui.whatsapp_callback = self.handle_whatsapp_message
#         self.move(990, 580)

#         for idx, choice in enumerate(choices[0:2]):
#             icon = setup_Icons(choice['app_name'], Icons_paths)
#             self.add_choice_main(choice['text'], idx, icon, self.on_clicked_choice)
#         self.ui.Close_Btn.clicked.connect(self.close)

#     def add_choice_main(self, text, id=None, icon_path= None, on_click = None):
#         self.ui.add_choice(text, id, icon_path, on_click)

#     def on_clicked_choice(self, content, id):
#         selected = self.allchoices[id]
#         self.selectedChoice = selected
#         self.ui.selected_choice = selected  # Store for default query
        
#         if selected.get('app_name', '').lower() == 'youtube':
#             self.ui.show_search()
#             self.ui.search_input.setFocus()
#             default_query = selected.get('search_query', '')
#             self.ui.search_input.setPlaceholderText(f"e.g. {default_query}" if default_query else "Enter search query...")
#         # elif selected.get('app_name', '').lower() == 'telegram desktop':
#         #     self.ui.show_search("telegram")
#         #     self.ui.search_input.setFocus()
#         #     self.ui.search_input.setPlaceholderText("Enter Telegram username (e.g., @username)")
#         elif selected.get('app_name', '').lower() == 'whatsapp':
#             self.ui.show_search("whatsapp")
#             self.ui.search_input.setFocus()
#             self.ui.search_input.setPlaceholderText("Enter phone number (e.g., +1234567890)")
#         else:
#             print(f"Selected: {id},{content}")
#             self.close()

    
#     def handle_youtube_search(self, query):
#         if query is None:  # User cancelled
#             return
            
#         # Find the YouTube option
#         youtube_choice = None
#         for choice in self.allchoices:
#             if choice.get('app_name', '').lower() == 'youtube':
#                 youtube_choice = choice
#                 break
                
#         if youtube_choice:
#             # Update the choice with the custom query
#             youtube_choice['search_query'] = query
#             self.selectedChoice = youtube_choice
#             self.close()
#     #def show_recommendations(self, show):

#     def handle_telegram_search(self, username):
#         if not username or not username.strip():
#             QMessageBox.warning(self, "Input Error", "Please enter a Telegram username")
#             return
        
#         username = username.lstrip('@')

#          # Show processing dialog
#         progress = QMessageBox(self)
#         progress.setWindowTitle("Searching")
#         progress.setText(f"Searching for @{username}...")
#         progress.setStandardButtons(QMessageBox.NoButton)
#         progress.show()
#         QApplication.processEvents()
        
#         try:
#             user_id = self.get_telegram_user_id(username)
#             if user_id:
#                 # Process successful result
#                 telegram_choice = next(
#                     (c for c in self.allchoices 
#                     if c.get('app_name', '').lower() == 'telegram desktop'),
#                     None
#                 )
#                 if telegram_choice:
#                     telegram_choice.update({
#                         'telegram_user_id': user_id,
#                         'telegram_username': f"@{username}",
#                         'app_url': f"https://t.me/{username}"
#                     })
#                     self.selectedChoice = telegram_choice
#         except Exception as e:
#             QMessageBox.critical(self, "Search Error", f"Failed to search user: {str(e)}")
#         finally:
#             progress.close()
#             self.close()

#     def handle_whatsapp_message(self, phone_number, message):
#         if not phone_number or not phone_number.strip():
#             QMessageBox.warning(self, "Input Error", "Please enter a phone number")
#             return
            
#         # Clean and validate phone number format
#         phone_number = phone_number.strip()
#         if not phone_number.startswith('+94'):
#             phone_number = '+94' + phone_number.lstrip('+')
        
#         if not re.match(r'^\+94[0-9]{9}$', phone_number):
#             QMessageBox.warning(self, "Input Error", 
#                 "Please enter a valid Sri Lankan phone number (e.g., +94771234567)")
#             return

            
#         if not message or not message.strip():
#             QMessageBox.warning(self, "Input Error", "Please enter a message")
#             return
#         # Show processing dialog
#         progress = QMessageBox(self)
#         progress.setWindowTitle("Sending")
#         progress.setText(f"Sending message to {phone_number}...")
#         progress.setStandardButtons(QMessageBox.NoButton)
#         progress.show()
#         QApplication.processEvents()
#         try:
#             # Find the WhatsApp option
#             whatsapp_choice = next(
#                 (c for c in self.allchoices 
#                 if c.get('app_name', '').lower() == 'whatsapp'),
#                 None
#             )
#             if whatsapp_choice:
#                 whatsapp_choice.update({
#                     'phone_number': phone_number.strip(),
#                     'message': message.strip()
#                 })
#                 self.selectedChoice = whatsapp_choice
                
#                 # Send the message using pywhatkit
#                 pywhatkit.sendwhatmsg_instantly(
#                     phone_no=phone_number.strip(),
#                     message=message.strip(),
#                     wait_time=15,
#                     tab_close=True,
#                     close_time=3
#                 )
#         except Exception as e:
#             QMessageBox.critical(self, "Send Error", f"Failed to send message: {str(e)}")
#         finally:
#             progress.close()
#             self.close()


#     def configure_dpi_awareness(self):
#         """Multi-layered DPI awareness configuration"""
#         try:
#             # Windows API level (works on Windows 10 1607+)
#             ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
#         except:
#             try:
#                 # Fallback for older Windows versions
#                 ctypes.windll.user32.SetProcessDPIAware()
#             except:
#                 pass
        
#         # Qt level
#         os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
#         os.environ["QT_SCALE_FACTOR"] = "1"
#         os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
#         QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
#         QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

#     def setup_chrome_service(self):
#         """Robust ChromeDriver setup with multiple fallbacks"""
#         try:
#             # Method 1: Automatic management with proper ChromeType detection
#             driver_path = ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install()
#             service = Service(driver_path)
#             # Test the driver
#             options = Options()
#             options.add_argument("--headless")
#             test_driver = webdriver.Chrome(service=service, options=options)
#             test_driver.quit()
#             return service
#         except Exception as e:
#             print(f"ChromeDriver auto-install failed: {e}")
            
#             # # Method 2: Try common paths
#             # common_paths = [
#             #     "chromedriver.exe",
#             #     os.path.join(os.getenv("ProgramFiles"), "Google", "Chrome", "Application", "chromedriver.exe"),
#             #     os.path.join(os.getenv("ProgramFiles(x86)"), "Google", "Chrome", "Application", "chromedriver.exe")
#             # ]
            
#             # for path in common_paths:
#             #     if os.path.exists(path):
#             #         try:
#             #             service = Service(path)
#             #             # Test the driver
#             #             options = Options()
#             #             options.add_argument("--headless")
#             #             test_driver = webdriver.Chrome(service=service, options=options)
#             #             test_driver.quit()
#             #             return service
#             #         except Exception as e:
#             #             print(f"ChromeDriver at {path} failed: {e}")
#             #             continue
            
#             # # Method 3: Try system PATH
#             # try:
#             #     service = Service()
#             #     options = Options()
#             #     options.add_argument("--headless")
#             #     test_driver = webdriver.Chrome(service=service, options=options)
#             #     test_driver.quit()
#             #     return service
#             # except:
#             #     QMessageBox.critical(None, "ChromeDriver Error",
#             #         "Could not initialize ChromeDriver.\n\n"
#             #         "Please ensure:\n"
#             #         "1. Chrome is installed from https://www.google.com/chrome/\n"
#             #         "2. Matching ChromeDriver is downloaded from https://chromedriver.chromium.org/\n"
#             #         "3. ChromeDriver is placed in your project folder or system PATH")
#             #     return None

#     def get_telegram_user_id(self, username):
#         """Robust Telegram user ID extraction"""
#         if not self.chrome_service:
#             return None

#         options = Options()
#         options.add_argument("--headless")
#         options.add_argument("--disable-dev-shm-usage")
#         options.add_argument("--disable-gpu")
#         options.add_argument("--no-sandbox")
#         options.add_argument("--window-size=1280,720")
#         options.add_experimental_option("excludeSwitches", ["enable-logging"])
#         driver = None

#         try:
#             driver = webdriver.Chrome(service=self.chrome_service, options=options)
#             driver.get("https://web.telegram.org/")
            
#             # Show persistent dialog until user confirms scan
#             msg = QMessageBox(self)
#             msg.setWindowTitle("Telegram Login Required")
#             msg.setText("Please:\n1. Scan the QR code in the browser window\n2. Click OK when logged in")
#             msg.setStandardButtons(QMessageBox.Ok)
#             msg.exec()
            
#             # Search for user
#             search_box = WebDriverWait(driver, 30).until(
#                 EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Search"]'))
#             )
#             search_box.clear()
#             search_box.send_keys(username)
            
#             # Wait for and click user
#             user_element = WebDriverWait(driver, 10).until(
#                 EC.element_to_be_clickable((By.XPATH, f'//div[contains(@class, "ChatInfo") and contains(., "{username}")]'))
#             )
#             user_element.click()
            
#             # Extract ID from URL
#             WebDriverWait(driver, 10).until(
#                 lambda d: "#" in d.current_url
#             )
#             return driver.current_url.split("#")[-1]
            
#         except Exception as e:
#             QMessageBox.warning(self, "Search Error", 
#                 f"Failed to find Telegram user:\n{str(e)}\n\n"
#                 "Please ensure:\n"
#                 "1. You're logged in to Telegram Web\n"
#                 "2. The username exists in your contacts")
#             return None
#         finally:
#             if driver:
#                 driver.quit()

# def launch_window(options):
#     # Enable High-DPI scaling
#     os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
#     os.environ["QT_SCALE_FACTOR"] = "1"
#     os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
#     """Function to create and return the window instance"""
#     # app = QApplication.instance()
#     # if not app:
#     #     app = QApplication(sys.argv)
#     #     # Apply style sheet if needed
#     #     style_file = QFile("style.qss")
#     #     if style_file.open(QFile.ReadOnly | QFile.Text):
#     #         stream = QTextStream(style_file)
#     #         app.setStyleSheet(stream.readAll())

#     # Create application instance
#     app = QApplication(sys.argv)
    
#     # Apply styles if available
#     if os.path.exists("style.qss"):
#         with open("style.qss", "r") as f:
#             app.setStyleSheet(f.read())
    
#     # Create and show main window
#     # window = MainWindow(options)
#     # window.show()

    
#     window = MainWindow(choices=options)
#     window.show()
#     # Debug output
#     print("Application and window initialized:")
#     print(f"App: {app}")
#     print(f"Window: {window}")
#     return window, app

# if __name__ == "__main__":
#     app = QApplication(sys.argv)

#     options = [
#         {'text': 'Watch relaxing video'},
#         {'text': 'Watch funny video'}
#     ]
    
#     window = MainWindow(options)
#     window.show()
#     app.exec()
#     print("Final choice: ", window.selectedChoice)




##############################################################

# import ctypes
# import sys
# from utils.mainWindowInterface import InteraceMainwindow
# import os
# import sys
# import re
# import time
# import win32api
# import win32con
# import pywhatkit
# from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout
# from PySide6.QtCore import Qt
# from PySide6.QtGui import QIcon
# # Use these instead:
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager
# from webdriver_manager.core.os_manager import ChromeType

# Icons_paths = [
#         {"app_name": "YouTube","icon_path": "utils/res/Youtube.png"},
#         {"app_name": "Spotify","icon_path": "utils/res/Spotify.png"},
#         {"app_name": "Discord","icon_path": "utils/res/Discord.png"},
#         {"app_name": "Zoom","icon_path": "utils/res/Zoom.png"},
#         {"app_name": "Microsoft Teams","icon_path": "utils/res/Teams.png"},
#         {"app_name": "Skype","icon_path": "utils/res/Skype.png"},
#         {"app_name": "Telegram Desktop","icon_path": "utils/res/Telegram.png"},
#         {"app_name": "WhatsApp","icon_path": "utils/res/Whatsapp.png"},
#         {"app_name": "Microsoft Solitaire Collection","icon_path": "utils/res/Solitaire.png"},
#         {"app_name": "Default","icon_path": "utils/res/default_app.png"},
#     ]

# def setup_Icons(app_name, icon_paths):
#     default_icon = "utils/res/default_app.png"
#     icon_path = default_icon
    
#     for idx, icon in enumerate(icon_paths):
#         if app_name == icon['app_name']:
#             icon_path = icon['icon_path']
#             break
#     return icon_path

# class MainWindow(QMainWindow):
#     def __init__(self, choices):
#         super().__init__()
#         # Configure DPI awareness before UI setup
#         self.configure_dpi_awareness()

#         self.selectedChoice = None
#         self.allchoices = choices
#         self.setWindowFlag(Qt.FramelessWindowHint)
#         self.setAttribute(Qt.WA_TranslucentBackground)
#         self.ui = InteraceMainwindow()
#         self.ui.setupUi(self)

#         # Configure ChromeDriver
#         self.chrome_service = self.setup_chrome_service()

#         # Connect search callback
#         self.ui.search_callback = self.handle_youtube_search
#         # self.ui.telegram_search_callback = self.handle_telegram_search
#         # Connect signals
#         self.ui.send_btn.clicked.connect(self.handle_send_whatsapp)
#         self.ui.open_app_btn.clicked.connect(self.handle_open_whatsapp)
#         self.move(990, 580)

#         for idx, choice in enumerate(choices[0:2]):
#             icon = setup_Icons(choice['app_name'], Icons_paths)
#             self.add_choice_main(choice['text'], idx, icon, self.on_clicked_choice)
#         self.ui.Close_Btn.clicked.connect(self.close)

#     def add_choice_main(self, text, id=None, icon_path= None, on_click = None):
#         self.ui.add_choice(text, id, icon_path, on_click)

#     def on_clicked_choice(self, content, id):
#         selected = self.allchoices[id]
#         self.selectedChoice = selected
#         self.ui.selected_choice = selected  # Store for default query
        
#         if selected.get('app_name', '').lower() == 'youtube':
#             self.ui.show_search()
#             self.ui.search_input.setFocus()
#             default_query = selected.get('search_query', '')
#             self.ui.search_input.setPlaceholderText(f"e.g. {default_query}" if default_query else "Enter search query...")
#         # elif selected.get('app_name', '').lower() == 'telegram desktop':
#         #     self.ui.show_search("telegram")
#         #     self.ui.search_input.setFocus()
#         #     self.ui.search_input.setPlaceholderText("Enter Telegram username (e.g., @username)")
#         elif selected.get('app_name', '').lower() == 'whatsapp':
#             self.ui.show_whatsapp_interface()  
#         else:
#             print(f"Selected: {id},{content}")
#             self.close()

    
#     def handle_youtube_search(self, query):
#         if query is None:  # User cancelled
#             return
            
#         # Find the YouTube option
#         youtube_choice = None
#         for choice in self.allchoices:
#             if choice.get('app_name', '').lower() == 'youtube':
#                 youtube_choice = choice
#                 break
                
#         if youtube_choice:
#             # Update the choice with the custom query
#             youtube_choice['search_query'] = query
#             self.selectedChoice = youtube_choice
#             self.close()
#     #def show_recommendations(self, show):

#     def handle_telegram_search(self, username):
#         if not username or not username.strip():
#             QMessageBox.warning(self, "Input Error", "Please enter a Telegram username")
#             return
        
#         username = username.lstrip('@')

#          # Show processing dialog
#         progress = QMessageBox(self)
#         progress.setWindowTitle("Searching")
#         progress.setText(f"Searching for @{username}...")
#         progress.setStandardButtons(QMessageBox.NoButton)
#         progress.show()
#         QApplication.processEvents()
        
#         try:
#             user_id = self.get_telegram_user_id(username)
#             if user_id:
#                 # Process successful result
#                 telegram_choice = next(
#                     (c for c in self.allchoices 
#                     if c.get('app_name', '').lower() == 'telegram desktop'),
#                     None
#                 )
#                 if telegram_choice:
#                     telegram_choice.update({
#                         'telegram_user_id': user_id,
#                         'telegram_username': f"@{username}",
#                         'app_url': f"https://t.me/{username}"
#                     })
#                     self.selectedChoice = telegram_choice
#         except Exception as e:
#             QMessageBox.critical(self, "Search Error", f"Failed to search user: {str(e)}")
#         finally:
#             progress.close()
#             self.close()

#     def handle_send_whatsapp(self):
#         phone = self.ui.phone_input.text()
#         message = self.ui.message_input.toPlainText()
        
#         # Validate input
#         phone = self.format_phone(phone)
#         if not phone:
#             QMessageBox.warning(self, "Invalid Number", "Please enter valid Sri Lankan number")
#             return
            
#         if not message.strip():
#             QMessageBox.warning(self, "Empty Message", "Please enter a message")
#             return
            
#         # Show progress
#         progress = QMessageBox(self)
#         progress.setWindowTitle("Sending")
#         progress.setText(f"Sending to {phone}...")
#         progress.setStandardButtons(QMessageBox.NoButton)
#         progress.show()
        
#         try:
#             pywhatkit.sendwhatmsg_instantly(
#                 phone_no=phone,
#                 message=message,
#                 wait_time=15,
#                 tab_close=True,
#                 close_time=3
#             )
#             self.close()
#         except Exception as e:
#             QMessageBox.critical(self, "Error", f"Failed to send: {str(e)}")
#         finally:
#             progress.close()

#     def format_phone(self, phone):
#         phone = phone.strip()
#         if phone.startswith('0'):
#             return '+94' + phone[1:]
#         elif phone.startswith('+94'):
#             return phone
#         return None

#     def handle_open_whatsapp(self):
#         whatsapp_choice = next(
#             (c for c in self.allchoices 
#             if c.get('app_name', '').lower() == 'whatsapp'),
#             None
#         )
#         if whatsapp_choice:
#             whatsapp_choice['action'] = 'open_app'
#             self.selectedChoice = whatsapp_choice
#             self.close()

#     def configure_dpi_awareness(self):
#         """Multi-layered DPI awareness configuration"""
#         try:
#             # Windows API level (works on Windows 10 1607+)
#             ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
#         except:
#             try:
#                 # Fallback for older Windows versions
#                 ctypes.windll.user32.SetProcessDPIAware()
#             except:
#                 pass
        
#         # Qt level
#         os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
#         os.environ["QT_SCALE_FACTOR"] = "1"
#         os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
#         QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
#         QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

#     def setup_chrome_service(self):
#         """Robust ChromeDriver setup with multiple fallbacks"""
#         try:
#             # Method 1: Automatic management with proper ChromeType detection
#             driver_path = ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install()
#             service = Service(driver_path)
#             # Test the driver
#             options = Options()
#             options.add_argument("--headless")
#             test_driver = webdriver.Chrome(service=service, options=options)
#             test_driver.quit()
#             return service
#         except Exception as e:
#             print(f"ChromeDriver auto-install failed: {e}")
            
#             # # Method 2: Try common paths
#             # common_paths = [
#             #     "chromedriver.exe",
#             #     os.path.join(os.getenv("ProgramFiles"), "Google", "Chrome", "Application", "chromedriver.exe"),
#             #     os.path.join(os.getenv("ProgramFiles(x86)"), "Google", "Chrome", "Application", "chromedriver.exe")
#             # ]
            
#             # for path in common_paths:
#             #     if os.path.exists(path):
#             #         try:
#             #             service = Service(path)
#             #             # Test the driver
#             #             options = Options()
#             #             options.add_argument("--headless")
#             #             test_driver = webdriver.Chrome(service=service, options=options)
#             #             test_driver.quit()
#             #             return service
#             #         except Exception as e:
#             #             print(f"ChromeDriver at {path} failed: {e}")
#             #             continue
            
#             # # Method 3: Try system PATH
#             # try:
#             #     service = Service()
#             #     options = Options()
#             #     options.add_argument("--headless")
#             #     test_driver = webdriver.Chrome(service=service, options=options)
#             #     test_driver.quit()
#             #     return service
#             # except:
#             #     QMessageBox.critical(None, "ChromeDriver Error",
#             #         "Could not initialize ChromeDriver.\n\n"
#             #         "Please ensure:\n"
#             #         "1. Chrome is installed from https://www.google.com/chrome/\n"
#             #         "2. Matching ChromeDriver is downloaded from https://chromedriver.chromium.org/\n"
#             #         "3. ChromeDriver is placed in your project folder or system PATH")
#             #     return None

#     def get_telegram_user_id(self, username):
#         """Robust Telegram user ID extraction"""
#         if not self.chrome_service:
#             return None

#         options = Options()
#         options.add_argument("--headless")
#         options.add_argument("--disable-dev-shm-usage")
#         options.add_argument("--disable-gpu")
#         options.add_argument("--no-sandbox")
#         options.add_argument("--window-size=1280,720")
#         options.add_experimental_option("excludeSwitches", ["enable-logging"])
#         driver = None

#         try:
#             driver = webdriver.Chrome(service=self.chrome_service, options=options)
#             driver.get("https://web.telegram.org/")
            
#             # Show persistent dialog until user confirms scan
#             msg = QMessageBox(self)
#             msg.setWindowTitle("Telegram Login Required")
#             msg.setText("Please:\n1. Scan the QR code in the browser window\n2. Click OK when logged in")
#             msg.setStandardButtons(QMessageBox.Ok)
#             msg.exec()
            
#             # Search for user
#             search_box = WebDriverWait(driver, 30).until(
#                 EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Search"]'))
#             )
#             search_box.clear()
#             search_box.send_keys(username)
            
#             # Wait for and click user
#             user_element = WebDriverWait(driver, 10).until(
#                 EC.element_to_be_clickable((By.XPATH, f'//div[contains(@class, "ChatInfo") and contains(., "{username}")]'))
#             )
#             user_element.click()
            
#             # Extract ID from URL
#             WebDriverWait(driver, 10).until(
#                 lambda d: "#" in d.current_url
#             )
#             return driver.current_url.split("#")[-1]
            
#         except Exception as e:
#             QMessageBox.warning(self, "Search Error", 
#                 f"Failed to find Telegram user:\n{str(e)}\n\n"
#                 "Please ensure:\n"
#                 "1. You're logged in to Telegram Web\n"
#                 "2. The username exists in your contacts")
#             return None
#         finally:
#             if driver:
#                 driver.quit()

# def launch_window(options):
#     # Enable High-DPI scaling
#     os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
#     os.environ["QT_SCALE_FACTOR"] = "1"
#     os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
#     """Function to create and return the window instance"""
#     # app = QApplication.instance()
#     # if not app:
#     #     app = QApplication(sys.argv)
#     #     # Apply style sheet if needed
#     #     style_file = QFile("style.qss")
#     #     if style_file.open(QFile.ReadOnly | QFile.Text):
#     #         stream = QTextStream(style_file)
#     #         app.setStyleSheet(stream.readAll())

#     # Create application instance
#     app = QApplication(sys.argv)
    
#     # Apply styles if available
#     if os.path.exists("style.qss"):
#         with open("style.qss", "r") as f:
#             app.setStyleSheet(f.read())
    
#     # Create and show main window
#     # window = MainWindow(options)
#     # window.show()

    
#     window = MainWindow(choices=options)
#     window.show()
#     # Debug output
#     print("Application and window initialized:")
#     print(f"App: {app}")
#     print(f"Window: {window}")
#     return window, app

# if __name__ == "__main__":
#     app = QApplication(sys.argv)

#     options = [
#         {'text': 'Watch relaxing video'},
#         {'text': 'Watch funny video'}
#     ]
    
#     window = MainWindow(options)
#     window.show()
#     app.exec()
#     print("Final choice: ", window.selectedChoice)





#main_window interface 
# -*- coding: utf-8 -*-

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt, Signal, QPropertyAnimation
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget, QPushButton, QGroupBox)
from PySide6.QtWidgets import QLineEdit, QPushButton

class ClickableFrame(QFrame):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.normal_color = "rgba(239, 224, 225, 128)"
        self.hover_color = "rgba(239, 207, 207, 200)"  # Slightly brighter/lighter
        self.pressed_color = "rgba(239, 207, 207, 255)"  # Darker when pressed
        
        self.setStyleSheet(f"""
            ClickableFrame {{
                background-color: {self.normal_color};
                border-radius: 15px;
                border: 2px solid rgb(0, 255, 255);
            }}
        """)

    def enterEvent(self, event):
        self.setStyleSheet(f"""
            ClickableFrame {{
                background-color: {self.hover_color};
                border-radius: 15px;
                border: 2px solid rgb(0, 255, 255);
            }}
        """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.setStyleSheet(f"""
            ClickableFrame {{
                background-color: {self.normal_color};
                border-radius: 15px;
                border: 2px solid rgb(0, 255, 255);
            }}
        """)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setStyleSheet(f"""
                ClickableFrame {{
                    background-color: {self.pressed_color};
                    border-radius: 15px;
                    border: 2px solid rgb(0, 200, 200);
                }}
            """)
            self.clicked.emit()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setStyleSheet(f"""
            ClickableFrame {{
                background-color: {self.hover_color};
                border-radius: 15px;
                border: 2px solid rgb(0, 255, 255);
            }}
        """)
        super().mouseReleaseEvent(event)

class InteraceMainwindow(object):

    def add_choice(self, text="New Choice", id=None, icon_path=None, on_click=None):
        """Improved version with proper parameter usage"""
        choice_frame = ClickableFrame()
        choice_frame.setObjectName(text.replace(" ", "_"))  # Sanitize object name
        choice_frame.setMinimumSize(QSize(380, 60))
        choice_frame.setMaximumSize(QSize(380, 60))
        
        # Set style with proper selector
        choice_frame.setStyleSheet(f"""
        #{choice_frame.objectName()} {{
           
            border-radius: 15px;
            border: 2px solid rgb(0, 255, 255);
        }}
        #{choice_frame.objectName()}:hover {{
        }}
        #{choice_frame.objectName()}:pressed {{
        }}
        """)
        
        layout = QHBoxLayout(choice_frame)
        layout.setContentsMargins(5, 5, 5, 5)

        # Icon frame
        icon_frame = QFrame()
        icon_frame.setObjectName("ChoiceIcon")
        icon_frame.setFixedSize(QSize(60, 50))
        
        if icon_path:
            icon_frame.setStyleSheet(f"""
            #ChoiceIcon {{
                background-image: url({icon_path});
                background-position: center;
                background-repeat: no-repeat;
                border-radius: 15px;
            }}
            """)
        
        layout.addWidget(icon_frame)

        # Text frame
        text_frame = QFrame()
        text_label = QLabel(text)
        text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        text_label.setFont(QFont("Sans Serif", 11, QFont.Bold))
        
        text_layout = QVBoxLayout(text_frame)
        text_layout.addWidget(text_label)
        layout.addWidget(text_frame)

        # Connect click signal if provided
        if callable(on_click):
            choice_frame.clicked.connect(lambda: on_click(text,id))

        self.verticalLayout.addWidget(choice_frame)

    def setupUi(self, MainWindow):
        # ===== Main Window Setup =====
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(530, 240)
        MainWindow.setMinimumSize(QSize(527, 235))
        MainWindow.setMaximumSize(QSize(530, 240))
        MainWindow.setLayoutDirection(Qt.LeftToRight)

        # ===== Stylesheet =====
        MainWindow.setStyleSheet(u"""
        * {
            border: none;
            background-color: transparent;
            background: none;
            padding: 0;
            margin: 0;
        }                

        #ChoiceFrame {
            background-color: rgba(239, 207, 207, 100);
            border-radius: 15px;
        }

        #Icon {
            background-color: rgba(87, 117, 201, 0.392);
            border-image: url(utils/res/Icon.jpg);
            border-radius: 15px;
        }
                                 
        #Close_Btn {
	        border-radius: 15px;
        }
        """)

        # ===== Central Widget =====
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")

        # ===== Main Frame =====
        self.MainFrame = QFrame(self.centralwidget)
        self.MainFrame.setObjectName(u"MainFrame")
        self.MainFrame.setGeometry(QRect(9, 9, 511, 221))
        self.MainFrame.setMinimumSize(QSize(511, 221))
        self.MainFrame.setMaximumSize(QSize(511, 221))
        self.MainFrame.setFrameShape(QFrame.StyledPanel)
        self.MainFrame.setFrameShadow(QFrame.Raised)

        # ===== Hide element =====
        self.recommend_group = QGroupBox(self.MainFrame)
        self.recommend_group.setObjectName(u"Recommend_Group")

        # ===== Exit button =====
        self.Close_Btn = QPushButton(self.recommend_group)
        self.Close_Btn.setObjectName(u"Close_Btn")

        self.Close_Btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 30);
                border-radius: 3px;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 50);
            }
        """)

        self.Close_Btn.setEnabled(True)
        self.Close_Btn.setGeometry(QRect(10, 30, 31, 21))
        self.Close_Btn.setAutoFillBackground(False)
        icon = QIcon()
        icon.addFile(u"utils/res/close.png", QSize(), QIcon.Normal, QIcon.Off)
        self.Close_Btn.setIcon(icon)
        self.Close_Btn.raise_()

        # ===== Icon Frame =====
        self.Icon = QFrame(self.MainFrame)
        self.Icon.setObjectName(u"Icon")
        self.Icon.setGeometry(QRect(410, 0, 100, 100))
        self.Icon.setMinimumSize(QSize(100, 100))
        self.Icon.setBaseSize(QSize(100, 100))
        self.Icon.setFrameShape(QFrame.Box)
        self.Icon.setFrameShadow(QFrame.Raised)

        # ===== Choice Frame =====
        self.ChoiceFrame = QFrame(self.recommend_group)
        self.ChoiceFrame.setObjectName(u"ChoiceFrame")
        self.ChoiceFrame.setGeometry(QRect(10, 49, 421, 162))
        self.ChoiceFrame.setMinimumSize(QSize(421, 161))
        self.ChoiceFrame.setLayoutDirection(Qt.LeftToRight)
        self.ChoiceFrame.setFrameShape(QFrame.StyledPanel)
        self.ChoiceFrame.setFrameShadow(QFrame.Raised)

        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        self.ChoiceFrame.setSizePolicy(sizePolicy)

        self.verticalLayout = QVBoxLayout(self.ChoiceFrame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSpacing(9)
        self.verticalLayout.setContentsMargins(15, 18, 26, 15)

        # frame_1 = add_choice("Watch Something New", "youtube_resize.png")
        # self.verticalLayout.addWidget(frame_1)

        # frame_2 = add_choice("Watch Something New", "youtube_resize.png")
        # self.verticalLayout.addWidget(frame_2)

        # Raise elements
        self.ChoiceFrame.raise_()
        self.Icon.raise_()

        self.recommend_group.setVisible(True)
        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

        
        # Add search components (hidden by default)
        self.search_frame = QFrame(self.MainFrame)
        self.search_frame.setObjectName(u"SearchFrame")
        self.search_frame.setGeometry(QRect(10, 49, 421, 100))
        self.search_frame.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(239, 207, 207, 180),
                    stop:1 rgba(200, 230, 255, 180)
                );
                border-radius: 15px;
                border: 2px solid rgb(0, 180, 255);
            }
        """)
        self.search_frame.hide()
        
        self.search_input = QLineEdit(self.search_frame)
        self.search_input.setPlaceholderText("Enter search query...")
        self.search_input.setGeometry(QRect(20, 20, 300, 30))
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 200);
                border-radius: 10px;
                border: 1px solid rgb(0, 150, 255);
                padding: 5px;
                font-size: 12px;
            }
            QLineEdit:hover {
                background-color: rgba(255, 255, 255, 230);
                border: 1px solid rgb(0, 180, 255);
            }
            QLineEdit:focus {
                background-color: rgba(255, 255, 255, 240);
                border: 1px solid rgb(0, 200, 255);
            }
        """)
        
        self.search_button = QPushButton("Search", self.search_frame)
        self.search_button.setGeometry(QRect(330, 20, 70, 30))
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(100, 200, 255, 220),
                    stop:1 rgba(50, 150, 255, 220)
                );
                border-radius: 10px;
                border: 1px solid rgb(0, 150, 255);
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(120, 220, 255, 240),
                    stop:1 rgba(70, 170, 255, 240)
                );
                border: 1px solid rgb(0, 180, 255);
            }
            QPushButton:pressed {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(80, 180, 255, 240),
                    stop:1 rgba(30, 130, 255, 240)
                );
                border: 1px solid rgb(0, 200, 255);
                padding-top: 2px;
                padding-left: 2px;
            }
        """)
        self.search_button.clicked.connect(self.on_search_clicked)
        
        
        self.cancel_button = QPushButton("Cancel", self.search_frame)
        self.cancel_button.setGeometry(QRect(330, 60, 70, 30))
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 150, 150, 220),
                    stop:1 rgba(255, 100, 100, 220)
                );
                border-radius: 10px;
                border: 1px solid rgb(255, 100, 100);
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 170, 170, 240),
                    stop:1 rgba(255, 120, 120, 240)
                );
                border: 1px solid rgb(255, 120, 120);
            }
            QPushButton:pressed {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 130, 130, 240),
                    stop:1 rgba(255, 80, 80, 240)
                );
                border: 1px solid rgb(255, 140, 140);
                padding-top: 2px;
                padding-left: 2px;
            }
        """)


    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))

    def updateLayoutShow(self, Recommend_Group):
        self.recommend_group.setVisible(True)
    
    def show_search(self, search_type="youtube"):
        """Show search frame with type-specific settings"""
        self.search_frame.setVisible(True)
        self.ChoiceFrame.setVisible(False)
        
        if search_type == "telegram":
            self.search_input.setPlaceholderText("Enter Telegram username (e.g., @username)")
            self.search_button.setText("Find User")
        else:  # youtube
            self.search_input.setPlaceholderText("Enter search query...")
            self.search_button.setText("Search")

    def on_search_clicked(self):
        search_query = self.search_input.text()
        # Emit signal or handle the search query
        # If no query was entered, use the default from the selected choice
        if not search_query:
            if hasattr(self, 'selected_choice'):
                search_query = self.selected_choice.get('search_query', '')
        
        # Determine which callback to use based on placeholder text
        if "Telegram username" in self.search_input.placeholderText():
            if hasattr(self, 'telegram_search_callback'):
                self.telegram_search_callback(search_query)
        else:
            if hasattr(self, 'search_callback'):
                self.search_callback(search_query)
        self.show_search(False)

    def on_cancel_clicked(self):
        self.show_search(False)
        if hasattr(self, 'search_callback'):
            self.search_callback(None)



#new main


# -*- coding: utf-8 -*-

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt, Signal, QPropertyAnimation
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget, QPushButton, QGroupBox)
from PySide6.QtWidgets import QLineEdit, QPushButton
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator

class ClickableFrame(QFrame):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.normal_color = "rgba(239, 224, 225, 128)"
        self.hover_color = "rgba(239, 207, 207, 200)"  # Slightly brighter/lighter
        self.pressed_color = "rgba(239, 207, 207, 255)"  # Darker when pressed
        
        self.setStyleSheet(f"""
            ClickableFrame {{
                background-color: {self.normal_color};
                border-radius: 15px;
                border: 2px solid rgb(0, 255, 255);
            }}
        """)

    def enterEvent(self, event):
        self.setStyleSheet(f"""
            ClickableFrame {{
                background-color: {self.hover_color};
                border-radius: 15px;
                border: 2px solid rgb(0, 255, 255);
            }}
        """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.setStyleSheet(f"""
            ClickableFrame {{
                background-color: {self.normal_color};
                border-radius: 15px;
                border: 2px solid rgb(0, 255, 255);
            }}
        """)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setStyleSheet(f"""
                ClickableFrame {{
                    background-color: {self.pressed_color};
                    border-radius: 15px;
                    border: 2px solid rgb(0, 200, 200);
                }}
            """)
            self.clicked.emit()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setStyleSheet(f"""
            ClickableFrame {{
                background-color: {self.hover_color};
                border-radius: 15px;
                border: 2px solid rgb(0, 255, 255);
            }}
        """)
        super().mouseReleaseEvent(event)

class InteraceMainwindow(object):

    def add_choice(self, text="New Choice", id=None, icon_path=None, on_click=None):
        """Improved version with proper parameter usage"""
        choice_frame = ClickableFrame()
        choice_frame.setObjectName(text.replace(" ", "_"))  # Sanitize object name
        choice_frame.setMinimumSize(QSize(380, 60))
        choice_frame.setMaximumSize(QSize(380, 60))
        
        # Set style with proper selector
        choice_frame.setStyleSheet(f"""
        #{choice_frame.objectName()} {{
           
            border-radius: 15px;
            border: 2px solid rgb(0, 255, 255);
        }}
        #{choice_frame.objectName()}:hover {{
        }}
        #{choice_frame.objectName()}:pressed {{
        }}
        """)
        
        layout = QHBoxLayout(choice_frame)
        layout.setContentsMargins(5, 5, 5, 5)

        # Icon frame
        icon_frame = QFrame()
        icon_frame.setObjectName("ChoiceIcon")
        icon_frame.setFixedSize(QSize(60, 50))
        
        if icon_path:
            icon_frame.setStyleSheet(f"""
            #ChoiceIcon {{
                background-image: url({icon_path});
                background-position: center;
                background-repeat: no-repeat;
                border-radius: 15px;
            }}
            """)
        
        layout.addWidget(icon_frame)

        # Text frame
        text_frame = QFrame()
        text_label = QLabel(text)
        text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        text_label.setFont(QFont("Sans Serif", 11, QFont.Bold))
        
        text_layout = QVBoxLayout(text_frame)
        text_layout.addWidget(text_label)
        layout.addWidget(text_frame)

        # Connect click signal if provided
        if callable(on_click):
            choice_frame.clicked.connect(lambda: on_click(text,id))

        self.verticalLayout.addWidget(choice_frame)

    def setupUi(self, MainWindow):
        # ===== Main Window Setup =====
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(530, 240)
        MainWindow.setMinimumSize(QSize(527, 235))
        MainWindow.setMaximumSize(QSize(530, 240))
        MainWindow.setLayoutDirection(Qt.LeftToRight)

        # ===== Stylesheet =====
        MainWindow.setStyleSheet(u"""
        * {
            border: none;
            background-color: transparent;
            background: none;
            padding: 0;
            margin: 0;
        }                

        #ChoiceFrame {
            background-color: rgba(239, 207, 207, 100);
            border-radius: 15px;
        }

        #Icon {
            background-color: rgba(87, 117, 201, 0.392);
            border-image: url(utils/res/Icon.jpg);
            border-radius: 15px;
        }
                                 
        #Close_Btn {
	        border-radius: 15px;
        }
        """)

        # ===== Central Widget =====
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.MainFrame.setGeometry(QRect(9, 9, 511, 221))

        # ===== Main Frame =====
        self.MainFrame = QFrame(self.centralwidget)
        self.MainFrame.setObjectName(u"MainFrame")
        self.MainFrame.setGeometry(QRect(9, 9, 511, 221))
        self.MainFrame.setMinimumSize(QSize(511, 221))
        self.MainFrame.setMaximumSize(QSize(511, 221))
        self.MainFrame.setFrameShape(QFrame.StyledPanel)
        self.MainFrame.setFrameShadow(QFrame.Raised)

        # ===== Hide element =====
        # Recommendation Group (main interface)
        self.recommend_group = QGroupBox(self.MainFrame)
        self.recommend_group.setObjectName(u"Recommend_Group")

        # ===== Exit button =====
        self.Close_Btn = QPushButton(self.recommend_group)
        self.Close_Btn.setObjectName(u"Close_Btn")

        self.Close_Btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 30);
                border-radius: 3px;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 50);
            }
        """)

        self.Close_Btn.setEnabled(True)
        self.Close_Btn.setGeometry(QRect(10, 30, 31, 21))
        self.Close_Btn.setAutoFillBackground(False)
        icon = QIcon()
        icon.addFile(u"utils/res/close.png", QSize(), QIcon.Normal, QIcon.Off)
        self.Close_Btn.setIcon(icon)
        self.Close_Btn.raise_()

        # ===== Icon Frame =====
        self.Icon = QFrame(self.MainFrame)
        self.Icon.setObjectName(u"Icon")
        self.Icon.setGeometry(QRect(410, 0, 100, 100))
        self.Icon.setMinimumSize(QSize(100, 100))
        self.Icon.setBaseSize(QSize(100, 100))
        self.Icon.setFrameShape(QFrame.Box)
        self.Icon.setFrameShadow(QFrame.Raised)

        # ===== Choice Frame =====
        self.ChoiceFrame = QFrame(self.recommend_group)
        self.ChoiceFrame.setObjectName(u"ChoiceFrame")
        self.ChoiceFrame.setGeometry(QRect(10, 49, 421, 162))
        self.ChoiceFrame.setMinimumSize(QSize(421, 161))
        self.ChoiceFrame.setLayoutDirection(Qt.LeftToRight)
        self.ChoiceFrame.setFrameShape(QFrame.StyledPanel)
        self.ChoiceFrame.setFrameShadow(QFrame.Raised)

        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        self.ChoiceFrame.setSizePolicy(sizePolicy)

        self.verticalLayout = QVBoxLayout(self.ChoiceFrame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSpacing(9)
        self.verticalLayout.setContentsMargins(15, 18, 26, 15)

        # frame_1 = add_choice("Watch Something New", "youtube_resize.png")
        # self.verticalLayout.addWidget(frame_1)

        # frame_2 = add_choice("Watch Something New", "youtube_resize.png")
        # self.verticalLayout.addWidget(frame_2)

        # Raise elements
        self.ChoiceFrame.raise_()
        self.Icon.raise_()

        self.recommend_group.setVisible(True)
        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

        
        # Add search components (hidden by default)
        self.search_frame = QFrame(self.MainFrame)
        self.search_frame.setObjectName(u"SearchFrame")
        self.search_frame.setGeometry(QRect(10, 49, 421, 162))
        self.search_frame.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(239, 207, 207, 180),
                    stop:1 rgba(200, 230, 255, 180)
                );
                border-radius: 15px;
                border: 2px solid rgb(0, 180, 255);
            }
        """)
        self.search_frame.hide()
        
        self.search_input = QLineEdit(self.search_frame)
        self.search_input.setPlaceholderText("Enter search query...")
        self.search_input.setGeometry(QRect(20, 20, 300, 30))
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 200);
                border-radius: 10px;
                border: 1px solid rgb(0, 150, 255);
                padding: 5px;
                font-size: 12px;
            }
            QLineEdit:hover {
                background-color: rgba(255, 255, 255, 230);
                border: 1px solid rgb(0, 180, 255);
            }
            QLineEdit:focus {
                background-color: rgba(255, 255, 255, 240);
                border: 1px solid rgb(0, 200, 255);
            }
        """)
        
        self.search_button = QPushButton("Search", self.search_frame)
        self.search_button.setGeometry(QRect(330, 20, 70, 30))
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(100, 200, 255, 220),
                    stop:1 rgba(50, 150, 255, 220)
                );
                border-radius: 10px;
                border: 1px solid rgb(0, 150, 255);
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(120, 220, 255, 240),
                    stop:1 rgba(70, 170, 255, 240)
                );
                border: 1px solid rgb(0, 180, 255);
            }
            QPushButton:pressed {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(80, 180, 255, 240),
                    stop:1 rgba(30, 130, 255, 240)
                );
                border: 1px solid rgb(0, 200, 255);
                padding-top: 2px;
                padding-left: 2px;
            }
        """)
        self.search_button.clicked.connect(self.on_search_clicked)
        
        
        self.cancel_button = QPushButton("Cancel", self.search_frame)
        self.cancel_button.setGeometry(QRect(330, 60, 70, 30))
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 150, 150, 220),
                    stop:1 rgba(255, 100, 100, 220)
                );
                border-radius: 10px;
                border: 1px solid rgb(255, 100, 100);
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 170, 170, 240),
                    stop:1 rgba(255, 120, 120, 240)
                );
                border: 1px solid rgb(255, 120, 120);
            }
            QPushButton:pressed {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 130, 130, 240),
                    stop:1 rgba(255, 80, 80, 240)
                );
                border: 1px solid rgb(255, 140, 140);
                padding-top: 2px;
                padding-left: 2px;
            }
        """)
        #Whatsapp part
        
        # WhatsApp Interface Widget
        self.whatsapp_widget = QFrame(self.MainFrame)
        self.whatsapp_widget.setObjectName(u"whatsapp_widget")
        self.whatsapp_widget.setGeometry(QRect(10, 49, 421, 162))
        self.whatsapp_widget.setStyleSheet("""
            QFrame {
                background-color: rgba(239, 207, 207, 180);
                border-radius: 15px;
                border: 2px solid rgb(0, 180, 255);
            }
        """)
        self.whatsapp_widget.hide()
        
        # WhatsApp UI Elements
        self.phone_input = QLineEdit(self.whatsapp_widget)
        self.phone_input.setGeometry(QRect(20, 20, 300, 30))
        self.phone_input.setPlaceholderText("+94712345678 or 0712345678")
        
        self.message_input = QTextEdit(self.whatsapp_widget)
        self.message_input.setGeometry(QRect(20, 60, 300, 80))
        self.message_input.setPlaceholderText("Type your message here...")
        
        self.send_btn = QPushButton("Send", self.whatsapp_widget)
        self.send_btn.setGeometry(QRect(330, 20, 70, 30))
        
        self.open_app_btn = QPushButton(self.whatsapp_widget)
        self.open_app_btn.setGeometry(QRect(330, 60, 70, 30))
        self.open_app_btn.setIcon(QIcon("utils/res/Whatsapp.png"))
        self.open_app_btn.setToolTip("Open WhatsApp")

        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def show_whatsapp_interface(self):
        """Show WhatsApp interface and hide choices"""
        self.whatsapp_widget.show()
        self.ChoiceFrame.hide()
        self.phone_input.setFocus()


    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))

    def updateLayoutShow(self, Recommend_Group):
        self.recommend_group.setVisible(True)
    
    def show_search(self, search_type="youtube"):
        """Show search frame with type-specific settings"""
        self.search_frame.setVisible(True)
        self.ChoiceFrame.setVisible(False)
        
        if search_type == "telegram":
            self.search_input.setPlaceholderText("Enter Telegram username (e.g., @username)")
            self.search_button.setText("Find User")
            
        else:  # youtube
            self.search_input.setPlaceholderText("Enter search query...")
            self.search_button.setText("Search")

    def on_search_clicked(self):
        search_query = self.search_input.text()
        # Emit signal or handle the search query
        # If no query was entered, use the default from the selected choice
        if not search_query:
            if hasattr(self, 'selected_choice'):
                search_query = self.selected_choice.get('search_query', '')
        
        # Determine which callback to use based on placeholder text
        if "Telegram username" in self.search_input.placeholderText():
            if hasattr(self, 'telegram_search_callback'):
                self.telegram_search_callback(search_query)
        else:
            if hasattr(self, 'search_callback'):
                self.search_callback(search_query)
        self.show_search(False)

    def on_cancel_clicked(self):
        self.show_search(False)
        if hasattr(self, 'search_callback'):
            self.search_callback(None)

    