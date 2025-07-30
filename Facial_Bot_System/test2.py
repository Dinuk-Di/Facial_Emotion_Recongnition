import threading
import time
import win32api # New import
import win32con # New import
import psutil
from typing import Dict, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.notifications import send_notification

launched_apps = {}
opened_apps_info = [] 
opened_browser_tabs: List[Dict] = []  
thread = None
# Timeout duration in seconds (15 minutes)
APP_TIMEOUT_SECONDS = 30
APP_WARNING_SECONDS = 20

def app_execution():

    win32api.ShellExecute(
        0,                      # hwnd: handle to parent window (0 for no parent)
        "open",                 # operation: "open", "print", "edit", "explore", "find"
        "explorer.exe",         # file: The program to execute (explorer.exe for shell:Appsfolder)
        r"shell:Appsfolder\Microsoft.MicrosoftSolitaireCollection_8wekyb3d8bbwe!App",           # parameters: The AUMID as a shell URI
        None,                   # directory: default directory
        win32con.SW_SHOWNORMAL  # show command: how the application is shown
    )
    time.sleep(2)  # Give app time to launch
    processes = []
    for proc in psutil.process_iter(['name']):
        if proc.info['name'].lower() == "solitaire.exe":
            processes.append(proc)

    if processes:
        opened_apps_info.append({
            'type': 'desktop',
            'processes': processes,
            'app_name': "Microsoft Solitaire Collection",
            'opened_at': time.time()
        })
        print("opened app info aumid process: ", opened_apps_info)
   

    win32api.ShellExecute(
        0,                           # hwnd
        "open",                      # operation
        r"C:\Users\Nuwani\AppData\Local\Microsoft\WindowsApps\ms-teams.exe",             # file: the path to the executable or shortcut
        None,                        # parameters (not needed for simple open)
        None,                        # directory
        win32con.SW_SHOWNORMAL       # show command
    )
    
    time.sleep(2)  # Give app time to launch
    matching_procs = []
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'].lower() == "ms-teams.exe":
                matching_procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if matching_procs:
        # Save the list of processes instead of single process
        opened_apps_info.append({
            'type': 'desktop',
            'processes': matching_procs,
            'app_name': "Microsoft Teams",
            'opened_at': time.time()
        })
        print("opened_app_info : ",opened_apps_info)



    # url = "https://www.youtube.com"
    # search = "Play relaxing music".replace(" ", "+")
    # url += f"/results?search_query={search}"
    #     # Open new Selenium browser window each time
    # options = webdriver.ChromeOptions()
    # options.add_argument("--new-window")  # Open in new window
    # driver = webdriver.Chrome(options=options)
    # driver.get(url)

    # opened_apps_info.append({
    #     'type': 'web',
    #     'driver': driver,
    #     'url': url,
    #     'opened_at': time.time()
    # })
    # if os.path.isdir(app_path_to_use):
    #     subprocess.Popen(f'start "" "{app_path_to_use}"', shell=True)
    #     return f"Opened folder for {app_info['name']}: {app_path_to_use}. (App might not launch directly from folder path)"
    
    # subprocess.Popen(f'"{app_path_to_use}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    start_monitoring_thread()

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
    

if __name__ == "__main__":
    app_execution()

