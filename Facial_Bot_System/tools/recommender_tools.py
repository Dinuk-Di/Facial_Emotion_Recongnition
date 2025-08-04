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
open_app = True

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

def signal_function(signal):
    global open_app
    open_app = signal

def open_recommendation(recommendation: dict) -> str:

    global launched_apps, opened_browser_tabs, opened_apps_info, open_app

    print(f"[Open_recommendation] {recommendation}")
    url = recommendation.get("app_url", "")
    app_name = recommendation.get("app_name", "")
    app_name_lower = app_name.lower()

    open_app = True
    print("Selected tool is: ", app_name_lower)
    if app_name_lower == "whatsapp":
        print("Whatsapp is selected")

        if recommendation["action"] == "open_app":
            print("Whatsapp window opened")
            open_app = True
            print("open_app: ", open_app)
        elif recommendation["action"] == "send_message":
            open_app = False
            print("open_app: ", open_app)

    if open_app:
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