
from PySide6.QtWidgets import QApplication, QMessageBox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import time
import pickle
import os
import json
import re

# Config
SESSION_DIR = "telegram_session"
COOKIES_FILE = os.path.join(SESSION_DIR, "cookies.pkl")
LOCAL_STORAGE_FILE = os.path.join(SESSION_DIR, "local_storage.json")
SESSION_STORAGE_FILE = os.path.join(SESSION_DIR, "session_storage.json")


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
        user_id = get_telegram_user_id(username)
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

def do_manual_login(driver, phoneNumber):

    print("User manual loggin is started.")
    click_login_phone = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR,'button[class = "Button smaller primary text"]'))
    )
    click_login_phone.click()
    time.sleep(5)

    input_user_phone = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR,'input[id = "sign-in-phone-number"]'))
    )
    # input_user_phone.clear()
    input_user_phone.send_keys(phoneNumber)
    time.sleep(3)

    phone_number_submit = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR,'button[type = "submit"]'))
    )
    phone_number_submit.click()

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.input-message-input')))
    
    logged_in_user_id = get_logged_in_user_id_from_local_storage(driver)
    if logged_in_user_id:
        save_user_auth(logged_in_user_id)
        print(f"Logged-in user ID saved: {logged_in_user_id}")
    else:
        print("Failed to find logged-in user ID in localStorage")

    print("User manual loggin is done.")
   
    # Extract and save logged-in user ID

def load_local_storage(driver):
        # Load localStorage
    if os.path.exists(LOCAL_STORAGE_FILE):
        with open(LOCAL_STORAGE_FILE, "r") as f:
            local_storage = json.load(f)
            for key, value in local_storage.items():
                driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")


def get_logged_in_user_id_from_local_storage(driver):
    print("inside the get_logged_in_user_id_from_ocal_storage")
    user_auth_json = driver.execute_script("return window.localStorage.getItem('user_auth');")
    print("user_auth_json: ", user_auth_json)
    if user_auth_json:
        try:
            user_auth = json.loads(user_auth_json)
            print("user_auth: ", user_auth)
            user_id = user_auth.get("id")
            print("user_auth_id: ", user_id)
            return user_id
        except Exception as e:
            print(f"Failed to parse user_auth JSON: {e}")
            return None
    return None

def save_user_auth(user_id):
    os.makedirs(SESSION_DIR, exist_ok=True)
    with open(os.path.join(SESSION_DIR, "user_auth.json"), "w") as f:
        json.dump({"id": user_id}, f)

def load_user_auth():
    path = os.path.join(SESSION_DIR, "user_auth.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
            return data.get("id")
    return None


def get_telegram_user_id(chrome_service, username, phoneNumber):
        """Robust Telegram user ID extraction"""
        #config
        COOKIES_FILE = "telegram_cookies.pkl"
        if not chrome_service:
            return None

        options = Options()
        # options.add_argument("--headless")  # Run in background
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=OFF")
        options.add_argument("--silent")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.images": 2,
        })
        driver = None

        try:
            driver = webdriver.Chrome(service=chrome_service, options=options)
            driver.get("https://web.telegram.org/a/")
            time.sleep(12)

            if not load_user_auth():
                print("Came to manual login")
                do_manual_login(driver, phoneNumber)
           
            # Refresh to apply cookies
            driver.get("https://web.telegram.org/a/")
            WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.input-message-input')))

            # WebDriverWait(driver, 10).until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, 'div.input-message-input'))
            # )
            # msg = QMessageBox()
            # msg.setWindowTitle("Telegram Login Required")
            # msg.setText("Please:\n1. Scan the QR code in the browser window\n2. Click OK when logged in")
            # msg.setStandardButtons(QMessageBox.Ok)
            # msg.exec()
            
            # Search for user
            print("Came up to search")

            search_box = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input.input-field-input'))
            )
            search_box.clear()
            search_box.send_keys(username)
            time.sleep(8)
            print("Search Executed")
            # Wait for and click user
            user_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f'//span[contains(@class, "peer-title") and contains(text(), "{username}")]'))
            )

            # # Wait for the URL to update containing the user's numeric ID hash (#<userid>)
            # WebDriverWait(driver, 10).until(lambda d: '#' in d.current_url)
            # current_url = driver.current_url
            # match = re.search(r'#(\d+)', current_url)
            # searched_user_id = match.group(1) if match else None

            # Extract the user ID from the data-peer-id attribute on the <span>
            searched_user_id = user_element.get_attribute("data-peer-id")
            # Click to open chat (optional, if you need to open chat before calling)
            user_element.click()
            print(f"Searched user ID (from data-peer-id): {searched_user_id}")

         
            call_telegram_user_by_id(setup_chrome_service(), searched_user_id)
            
        except Exception as e:
            # QMessageBox.warning( "Search Error", 
            #     f"Failed to find Telegram user:\n{str(e)}\n\n"
            #     "Please ensure:\n"
            #     "1. You're logged in to Telegram Web\n"
            #     "2. The username exists in your contacts")
            print("error; ", e)
            return None
        finally:
            if driver:
                driver.quit()

def call_telegram_user_by_id(chrome_service, user_id):
    options = Options()
    # Keep browser visible to handle complex UI elements reliably
    # options.add_argument("--headless")  # Uncomment if you want headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Chrome(service=chrome_service, options=options)

    try:
        # Open Telegram Web chat by user ID
        url = f"https://web.telegram.org/k/#{user_id}"
        driver.get(url)

        # Wait until chat interface loads
        # The message input box presence indicates chat is ready
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.input-message-input"))
        )
        
        print(f"Chat with user ID {user_id} loaded.")

        # Wait a short time to fully stabilize UI for call button appearance
        time.sleep(5)

        # Try to find the call button - Telegram Web call button's selector needs confirmation via inspecting Telegram Web UI
        # It might have aria-label "Start voice call" or a specific class
        # Example XPath assuming button title or aria-label contains 'call'
        try:
            call_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'btn-icon rp')]")
                )
            ) 
            call_button.click()
            print("Call button clicked. Call should be initiated.")
        except Exception as e:
            print("Could not find or click the call button:", e)
        
        # Optionally, keep the browser open for call duration or close after delay
        time.sleep(10)  # Wait 10 seconds in call before closing - adjust as needed

    finally:
        driver.quit()

def setup_chrome_service():
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
        print("driver is downloaded:", service)
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

def main():

    try:
        # options = Options()
        # # options.add_argument("--headless")  # Run in background
        # options.add_argument("--disable-gpu")
        # options.add_argument("--log-level=OFF")
        # options.add_argument("--silent")
        # options.add_argument("--disable-notifications")
        # options.add_argument("--disable-infobars")
        # options.add_argument("--disable-extensions")
        # options.add_argument("--disable-dev-shm-usage")
        # options.add_argument("--no-sandbox")
        # options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        # options.add_experimental_option("prefs", {
        #     "profile.default_content_setting_values.notifications": 2,
        #     "profile.managed_default_content_settings.images": 2,
        # })
        
        # driver = webdriver.Chrome(service=setup_chrome_service(), options=options)
        # driver.get("https://web.telegram.org/a/")

        get_telegram_user_id(setup_chrome_service(), "Dinuk", '777073972')
    except KeyboardInterrupt:
        print("Exiting...")
        # Daemon thread will exit automatically

if __name__ == "__main__":
    main()