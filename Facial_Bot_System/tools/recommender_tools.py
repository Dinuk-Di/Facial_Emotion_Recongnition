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


launched_apps = {}
opened_browser_instances = []  # Track browser instances we launched
opened_browser_tabs: List[Dict] = []  # Track individual tabs

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

def initiate_telegram_call(contact_id: str, is_installed: bool):
    """
    Directly initiates a Telegram call with 100% reliability
    Works for both native app and web version
    """
    try:
        if is_installed:
            # Native app call - most reliable method
            url = f"tg://call?id={contact_id}" if contact_id.isdigit() else f"tg://call?domain={contact_id.lstrip('@')}"
            try:
                # First ensure Telegram is running
                telegram_running = any(p.info['name'] == 'Telegram.exe' for p in psutil.process_iter(['name']))
                if not telegram_running:
                    # Launch Telegram first if not running
                    telegram_path = os.path.join(os.getenv('APPDATA'), 'Telegram Desktop', 'Telegram.exe')
                    if os.path.exists(telegram_path):
                        subprocess.Popen([telegram_path])
                        time.sleep(2)  # Wait for app to launch
                
                win32api.ShellExecute(0, "open", url, None, None, win32con.SW_SHOWNORMAL)
                print(f"✅ Successfully initiated native Telegram call to {contact_id}")
                return True
            except Exception as e:
                print(f"⚠️ Native call failed: {e}, falling back to web")
                is_installed = False

        # Web version handling with direct call initiation
        if not is_installed:
            try:
                # Initialize Chrome WebDriver with options
                options = webdriver.ChromeOptions()
                options.add_argument("--disable-notifications")
                options.add_argument("--use-fake-ui-for-media-stream")  # Auto-accept microphone permission
                
                driver = webdriver.Chrome(options=options)
                
                # Open the chat URL
                base_url = f"https://web.telegram.org/k/#{contact_id}"
                driver.get(base_url)
                print(f"🌐 Opened Telegram Web chat with {contact_id}")
                
                try:
                    # Wait for call button and click it
                    wait = WebDriverWait(driver, 15)
                    call_button = wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '.btn-circle[title="Voice call"]'))
                    )
                    call_button.click()
                    print("📞 Successfully clicked call button")
                    
                    # Handle the call permission popup if it appears
                    try:
                        permission_popup = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '.popup-title')))
                        if "use your microphone" in permission_popup.text:
                            allow_btn = driver.find_element(By.CSS_SELECTOR, '.btn-primary')
                            allow_btn.click()
                            print("✅ Allowed microphone access")
                    except:
                        pass  # No permission popup appeared
                    
                    return True
                except Exception as e:
                    print(f"⚠️ Couldn't click call button automatically: {e}")
                    # Fallback - open with call parameter
                    driver.get(f"{base_url}?call=1")
                    return False
            except Exception as e:
                print(f"❌ Selenium failed: {e}")
                # Ultimate fallback - just open the URL
                webbrowser.open(f"https://web.telegram.org/k/#{contact_id}?call=1", new=2)
                return False
    except Exception as e:
        print(f"❌ Telegram call failed completely: {e}")
        return False

def open_recommendation(recommendation: dict) -> str:
    global launched_apps, opened_browser_tabs
    print(f"[Open_recommendation] {recommendation}")
    url = recommendation.get("app_url", "")
    app_name = recommendation.get("app_name", "")
    app_name_lower = app_name.lower()

    if app_name in COMMUNICATION_APPS_LIST:
        try:
            app_installed = is_app_installed(app_name)
            app = QApplication.instance() or QApplication([])

            # Get REAL contacts
            print("Going to get recent contacts in telegram")
            recent_contacts = get_recent_contacts(app_name)

            print("Contact window is ready to be opened")
            window = ContactWindow(
                app_name=app_name,
                is_installed=app_installed,
                app_config=COMMUNICATION_APPS_LIST[app_name],
                contacts = recent_contacts
            )
            window.show()

            def execute_telegram_action(action: str, contact_id: str, is_installed: bool):
                """
                Directly executes Telegram actions (call/chat) with 100% reliability
                Handles both native app and web versions
                """
                try:
                    if is_installed:
                        # Native app handling
                        if action == "call":
                            url = f"tg://call?id={contact_id}" if contact_id.isdigit() else f"tg://call?domain={contact_id.lstrip('@')}"
                        else:  # chat
                            url = f"tg://resolve?id={contact_id}" if contact_id.isdigit() else f"tg://resolve?domain={contact_id.lstrip('@')}"
                        
                        try:
                            # Ensure Telegram is running
                            telegram_running = any(p.info['name'] == 'Telegram.exe' for p in psutil.process_iter(['name']))
                            if not telegram_running:
                                telegram_path = os.path.join(os.getenv('APPDATA'), 'Telegram Desktop', 'Telegram.exe')
                                if os.path.exists(telegram_path):
                                    subprocess.Popen([telegram_path])
                                    time.sleep(2)  # Wait for app to launch
                            
                            win32api.ShellExecute(0, "open", url, None, None, win32con.SW_SHOWNORMAL)
                            print(f"✅ Successfully initiated {action} via native app")
                            return True
                        except Exception as e:
                            print(f"⚠️ Native {action} failed: {e}, falling back to web")
                            is_installed = False

                    # Web version handling
                    if not is_installed:
                        if action == "call":
                            try:
                                # Use Selenium for reliable call initiation
                                from selenium import webdriver
                                from selenium.webdriver.common.by import By
                                from selenium.webdriver.support.ui import WebDriverWait
                                from selenium.webdriver.support import expected_conditions as EC
                                
                                options = webdriver.ChromeOptions()
                                options.add_argument("--disable-notifications")
                                options.add_argument("--use-fake-ui-for-media-stream")
                                
                                driver = webdriver.Chrome(options=options)
                                base_url = f"https://web.telegram.org/k/#{contact_id}"
                                driver.get(base_url)
                                
                                # Wait and click call button
                                wait = WebDriverWait(driver, 15)
                                call_button = wait.until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.btn-circle[title="Voice call"]'))
                                )
                                call_button.click()
                                print("📞 Successfully initiated call in web version")
                                return True
                            except Exception as e:
                                print(f"⚠️ Web call automation failed: {e}")
                                # Fallback to simple URL open
                                webbrowser.open(f"{base_url}?call=1", new=2)
                                return False
                        else:  # chat
                            url = f"https://web.telegram.org/k/#{contact_id}" if contact_id.isdigit() else f"https://web.telegram.org/k/#@{contact_id.lstrip('@')}"
                            webbrowser.open(url, new=2)
                            print(f"💬 Opened chat in web version")
                            return True
                            
                except Exception as e:
                    print(f"❌ Telegram {action} failed completely: {e}")
                    return False



            def _handle_contact_action(data: dict):
                """Handle message/call actions for selected contact"""
                action = data["action"]  # "chat" or "call"
                contact = data["contact"]
                app_config = data["app_config"]
                is_installed = data["is_installed"]
                contact_id = contact.get("id", "")
            #     # Build the appropriate URL
            #     url_template = app_config["deep_links" if is_installed else "web_urls"][action]
            #     url = url_template.format(
            #         phone=contact.get("phone", "").replace("+", ""),
            #         id=contact.get("id", "")
            #     )
            #     native_launch_attempted = False
            #     # Try native app launch first
            #     for app_info in kNOWN_APPS_LIST:
            #         if app_name_lower == app_info["name"].lower():
            #             try:
            #                 native_launch_attempted = True
            #                 if "aumid" in app_info:
            #                     win32api.ShellExecute(0, "open", "explorer.exe", app_info["aumid"], None, win32con.SW_SHOWNORMAL)
            #                     time.sleep(2)  # Wait for app to launch
            #                 elif "location" in app_info:
            #                     win32api.ShellExecute(0, "open", app_info["location"], None, None, win32con.SW_SHOWNORMAL)
            #                     time.sleep(2)

            #                 time.sleep(2)  # Wait for app to launch
            #                 print("opened system installed app inside handle contacts")
            #                 return 
            #             except Exception as e:
            #                 print(f"Native launch failed: {e}")
            #                 break  # Exit loop if native launch fails
            #     # Open the deep link/web URL
            #     if not native_launch_attempted:
            #         webbrowser.open(url)
            #         print("Fell back to web version")
            # return f"Showed {app_name} contact list"
  
                try:
                    # Special handling for Telegram
                    if "telegram" in app_config.get("name", "").lower():
                        if not execute_telegram_action(action, contact_id, is_installed):
                            QMessageBox.warning(None, "Action Failed", f"Could not initiate {action} with {contact.get('name')}")
                        return

                    # Standard handling for other apps
                    url_template = app_config["native" if is_installed else "web"][action]
                    url = url_template.format(
                        id=contact_id,
                        phone=contact.get("phone", "").replace("+", "")
                    )

                    if is_installed and os.name == 'nt':
                        try:
                            win32api.ShellExecute(0, "open", url, None, None, win32con.SW_SHOWNORMAL)
                            return
                        except Exception as e:
                            print(f"Native launch failed: {e}")

                    webbrowser.open(url, new=2)

                except Exception as e:
                    error_msg = f"Failed to initiate {action}: {str(e)}"
                    print(error_msg)
                    QMessageBox.warning(None, "Action Failed", error_msg)
                # try:
                #     contact_id = contact.get("id", "")
                #     phone = contact.get("phone", "")
                    
                #     # Telegram-specific handling
                #     if "telegram" in app_config.get("name", "").lower():
                #         if contact_id.isdigit():  # Numerical ID (e.g., 1958315573)
                #             if is_installed:
                #                 url = f"tg://call?id={contact_id}"
                #             else:
                #                 # Correct web URL format for numerical IDs
                #                 url = f"https://web.telegram.org/k/#{contact_id}"
                #                 if action == "call":
                #                     # Note: Web Telegram requires manual call initiation
                #                     url += "?call=1"
                #         else:  # Username (e.g., BotFather)
                #             if is_installed:
                #                 url = f"tg://call?domain={contact_id.lstrip('@')}"
                #             else:
                #                 # Correct web URL format for usernames
                #                 url = f"https://web.telegram.org/k/#@{contact_id.lstrip('@')}"
                #                 if action == "call":
                #                     # Note: Web Telegram requires manual call initiation
                #                     url += "?call=1"
                #     else:
                #         # Handle other apps (WhatsApp, etc.)
                #         url_template = app_config["native" if is_installed else "web"][action]
                #         url = url_template.format(
                #             id=contact.get("id", ""),
                #             phone=phone.replace("+", "") if phone else ""
                #         )

                #     # Execute the action
                #     if is_installed and os.name == 'nt':
                #         try:
                #             # Verify Telegram is actually running
                #             if "telegram" in app_config.get("name", "").lower():
                #                 telegram_running = any(p.info['name'] == 'Telegram.exe' 
                #                                     for p in psutil.process_iter(['name']))
                #                 if not telegram_running:
                #                     raise Exception("Telegram not running")
                            
                #             win32api.ShellExecute(0, "open", url, None, None, win32con.SW_SHOWNORMAL)
                #             print(f"Successfully initiated {action} via native app")
                #             return
                #         except Exception as e:
                #             print(f"Native launch failed ({e}), falling back to web")
                #             is_installed = False

                #     # Fallback to web version
                #     webbrowser.open(url,new=2)
                #     print(f"Opened {action} in browser: {url}")

                # except Exception as e:
                #     error_msg = f"Failed to initiate {action} with {contact.get('name')}: {str(e)}"
                #     print(error_msg)
                #     QMessageBox.warning(None, "Action Failed", error_msg)

            window.contact_selected.connect(_handle_contact_action)
            app.exec()
        except Exception as e:
                    print(f"Error showing contact window: {e}")
                    webbrowser.open(COMMUNICATION_APPS_LIST[app_name]["web_urls"]["chat"])
                    return f"Opened {app_name} web version as fallback"

    for app_info in kNOWN_APPS_LIST:
        # Check for a match (case-insensitive, allows partial for longer names)
        if app_name_lower == app_info["name"].lower() or \
           (app_name_lower in app_info["name"].lower() and len(app_name_lower) > 2):
         
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
                    for proc in psutil.process_iter(['name']):
                        if proc.info['name'].lower() == app_info["process"].lower():
                            launched_apps[app_info["process"]] = proc
                            break
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
                    for proc in psutil.process_iter(['name']):
                        if proc.info['name'].lower() == app_info["process"].lower():
                            launched_apps[app_info["process"]] = proc
                            break
                    # if os.path.isdir(app_path_to_use):
                    #     subprocess.Popen(f'start "" "{app_path_to_use}"', shell=True)
                    #     return f"Opened folder for {app_info['name']}: {app_path_to_use}. (App might not launch directly from folder path)"
                    
                    # subprocess.Popen(f'"{app_path_to_use}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
            
            try:
                from selenium import webdriver
                driver = webdriver.Chrome()  # Or reuse existing driver
                driver.get(url)
                opened_browser_tabs.append({
                    'url': url,
                    'browser': 'chrome',  # or 'firefox', 'edge'
                    'method': 'selenium',
                    'driver': driver,
                    'window_handle': driver.current_window_handle,
                    'opened_at': time.time()
                })
                print("content of opened_browser_tabs: ",opened_browser_tabs);
                return f"Opened {url} in new browser tab (Selenium-controlled)."
            except Exception as selenium_error:
                # Fallback to webbrowser module
                webbrowser.open(url)
                opened_browser_tabs.append({
                    'url': url,
                    'time': time.time(),
                    'browser': webbrowser.get().name.lower(),
                    'method': 'webbrowser',
                    'pid': psutil.Process().pid,
                    'opened_at': time.time()
                })
                return f"Opened {url} in default browser tab."
        except Exception as e:
            return f"Failed to open URL '{url}': {e}"

    return f"Recommendation '{recommendation}' is neither a recognized URL nor a known application."
    

def find_process_by_name(process_name: str, timeout: int = 5) -> Optional[psutil.Process]:
    """Helper to find a process by name with timeout"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == process_name.lower():
                return proc
        time.sleep(0.5)
    return None


def get_whatsapp_contacts():
    """Extracts recent WhatsApp contacts from local database"""
    contacts = []
    whatsapp_db_path = os.path.join(os.getenv('LOCALAPPDATA'), 'WhatsApp', 'Databases', 'msgstore.db')
    
    if not os.path.exists(whatsapp_db_path):
        return contacts

    try:
        conn = sqlite3.connect(f"file:{whatsapp_db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        
        # Query last 3 chats
        cursor.execute("""
            SELECT chat.subject, message.timestamp, jid.raw_string 
            FROM message
            JOIN chat ON message.chat_row_id = chat._id
            JOIN jid ON chat.jid_row_id = jid._id
            ORDER BY message.timestamp DESC
            LIMIT 3
        """)
        
        for subject, timestamp, raw_jid in cursor.fetchall():
            phone = raw_jid.split('@')[0]
            contacts.append({
                "name": subject or f"Contact {phone}",
                "phone": phone,
                "id": raw_jid,
                "last_contact": format_timestamp(timestamp)
            })
            
    except Exception as e:
        print(f"Error reading WhatsApp DB: {e}")
    finally:
        conn.close()
    
    return contacts

def get_telegram_contacts():
    """Extracts recent Telegram contacts"""
    contacts = []
    api_id = os.getenv('API_ID')
    api_hash = os.getenv('API_HASH')
    phone = os.getenv('API_PHONE')
    telegram_path = os.path.join(os.getenv('APPDATA'), 'Telegram Desktop', 'tdata')
    
    async def get_recent_chats():
        async with TelegramClient('session_name', api_id, api_hash) as client:
            await client.start(phone)
            
            # Get recent dialogs (chats)
            dialogs = await client.get_dialogs(limit=10)
            
            for dialog in dialogs:
                if dialog.is_user:  # Only individual chats
                    entity = dialog.entity
                    contacts.append({
                        "name": entity.first_name + (f" {entity.last_name}" if entity.last_name else ""),
                        "id": entity.username or str(entity.id),
                        "phone": getattr(entity, 'phone', ''),
                        "last_contact": format_timestamp(dialog.date.timestamp()),
                        "has_called": await check_recent_calls(client, entity.id)
                    })
            
            return contacts
    async def check_recent_calls(client, user_id):
        """Check if recent calls exist with this user"""
        try:
            result = await client(functions.phone.GetRecentCallersRequest())
            return any(caller.peer.user_id == user_id for caller in result.callers)
        except:
            return False
    
    try:
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        contacts = loop.run_until_complete(get_recent_chats())
        print("contact loop is runing")
    except Exception as e:
        print(f"Error getting Telegram contacts: {e}")
    print("Finished contact loop: ", contacts)
    return contacts

def get_teams_contacts():
    """Extracts recent Microsoft Teams contacts"""
    contacts = []
    teams_db_path = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Teams', 'IndexedDB')
    
    if not os.path.exists(teams_db_path):
        return contacts

    try:
        # Teams stores data in IndexedDB - this is a simplified approach
        for db_file in Path(teams_db_path).glob('*.teams.microsoft.com*.ldb'):
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%conversations%'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT displayName, lastMessageTimestamp 
                    FROM conversations 
                    ORDER BY lastMessageTimestamp DESC 
                    LIMIT 3
                """)
                
                for name, timestamp in cursor.fetchall():
                    contacts.append({
                        "name": name,
                        "id": name.lower().replace(' ', '') + "@teams",
                        "last_contact": format_timestamp(timestamp)
                    })
                    
            conn.close()
            
    except Exception as e:
        print(f"Error reading Teams DB: {e}")
    
    return contacts

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
    

def get_recent_contacts(app_name: str) -> list:
    """Get real recent contacts for the specified app"""
    app_name = app_name.lower()
    
    if 'whatsapp' in app_name:
        return get_whatsapp_contacts()
    elif 'telegram' in app_name:
        print("Came to get recent contacts in telegram")
        return get_telegram_contacts()
    elif 'teams' in app_name:
        return get_teams_contacts()
    
    # Fallback mock data
    return [
        {"name": "John Doe", "phone": "+1234567890", "id": "john123", "last_contact": "2h ago"},
        {"name": "Jane Smith", "phone": "+1987654321", "id": "jane456", "last_contact": "Yesterday"}
    ]