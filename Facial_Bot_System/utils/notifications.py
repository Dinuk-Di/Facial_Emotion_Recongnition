import win32api
import win32con
import win32gui
import subprocess
import webbrowser

def send_notification(title, message):
    win32api.MessageBox(0, message, title, win32con.MB_ICONINFORMATION)

def execute_task(recommendation):
    actions = {
        "Play music": lambda: webbrowser.open("https://open.spotify.com"),
        "Watch funny videos": lambda: webbrowser.open("https://www.youtube.com"),
        "Take a break": lambda: send_notification("Break Time", "Try deep breathing:\n1. Inhale 4s\n2. Hold 4s\n3. Exhale 6s"),
        "Quick game": lambda: webbrowser.open("https://www.chess.com"),
    }
    
    action = actions.get(recommendation, lambda: None)
    action()