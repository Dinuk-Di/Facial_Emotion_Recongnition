import ctypes
import sys
from utils.mainWindowInterface import InteraceMainwindow, WhatsAppWindow
import os
import sys
import re
import time
import win32api
import win32con
import pywhatkit
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import Qt, QFile, QTextStream, Signal
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
    openAppRequest = Signal(bool)
    def __init__(self, choices):
        super().__init__()

        self.selectedChoice = None
        self.allchoices = choices
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.ui = InteraceMainwindow()
        self.ui.setupUi(self)
        

        # Connect search callback
        self.ui.search_callback = self.handle_youtube_search
        self.ui.whatsapp_callback = self.handle_send_whatsapp_message
        
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
        
        app_name = selected.get('app_name', '').lower()
        if app_name == 'youtube':
            self.ui.show_search()
            self.ui.search_input.setFocus()
            default_query = selected.get('search_query', '')
            self.ui.search_input.setPlaceholderText(f"e.g. {default_query}" if default_query else "Enter search query...")
        elif app_name == 'whatsapp':
            # Instead of show_search, open the WhatsApp window aligned with main window
            self.open_whatsapp_window()
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

    def open_whatsapp_window(self):
        if self.ui.whatsapp_dialog is None:
            self.ui.whatsapp_dialog = WhatsAppWindow(parent=self)
            self.ui.whatsapp_dialog.sendMessageRequested.connect(self.handle_send_whatsapp_message)
            self.ui.whatsapp_dialog.openAppRequest.connect(self.handle_open_whatsapp)
        else:
            self.ui.whatsapp_dialog.show()
            self.ui.whatsapp_dialog.raise_()
            self.ui.whatsapp_dialog.activateWindow()

    def handle_send_whatsapp_message(self, phone, message):
        if not phone or not phone.startswith('+') or len(phone) < 8:
            QMessageBox.warning(self, "Input Error", "Please enter a valid phone number including country code and starting with '+'.")
            return
        if not message:
            QMessageBox.warning(self, "Input Error", "Please enter a message to send.")
            return

        # Optional: Additional phone number validation (e.g., country code format) can be added here.
        self.openAppRequest.emit(False)
        try:
            pywhatkit.sendwhatmsg_instantly(
                phone_no=phone,
                message=message,
                wait_time=15,
                tab_close=True,
                close_time=20
            )
            print("Message sent successfully")
            self.ui.whatsapp_dialog.close()
            print("Whasapp window closed successfully")
            QMessageBox.information(self, "Success", f"WhatsApp message sent to {phone}")
            
        except Exception as e:
            self.ui.whatsapp_dialog.close()
            QMessageBox.critical(self, "Error", f"Failed to send WhatsApp message:\n{str(e)}")
    
    def handle_open_whatsapp(self, signal):
        self.openAppRequest.emit(signal)
        print("Signal for open app,openAppRequest: ", signal , self.openAppRequest)
        print("Whatsapp app opened successfully")
        self.ui.whatsapp_dialog.close()
        print("Whasapp window closed successfully")


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
        {'text': 'Send WhatsApp Message', 'app_name': 'WhatsApp'},
        {'text': 'Watch relaxing video'},
        {'text': 'Watch funny video'}
    ]
    
    window = MainWindow(options)
    window.show()
    app.exec()
    print("Final choice: ", window.selectedChoice)

