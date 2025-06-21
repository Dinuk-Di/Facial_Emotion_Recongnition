from win11toast import toast
import os
import subprocess
import threading

icon_path = r'F:/Academic/7th semester/FYP/recommondation_agents_implementation/assests/Icon.jpg'
executer_path = r'C:/Users/rpras/OneDrive/Documents/Rashmitha/Semester_7/project/Features/executer.pyw'

def notification_show(timeout=20):
    event = threading.Event()
    user_action = False

    if not os.path.exists(icon_path):
        print(f"Warning: Icon file not found at {icon_path}")
        icon = None
    else:
        icon = {
        'src': icon_path,
        'placement': 'appLogoOverride'
        }

    def on_click(*args):
        try:
            #subprocess.Popen(["pythonw", executer_path], shell=True)
            nonlocal user_action
            user_action = True
            event.set()
        except Exception as e:
            print(f"Error executing script: {e}")

    # def on_click():
    #     try:
    #         print("Clicked")
    #     except Exception as e:
    #         print(f"Error executing script: {e}")

    toast('Emotion Recognition Test', 'Click here to check out content', icon=icon,  app_id="EMOFI", on_click=on_click, button='Dismiss')

    event.wait(timeout=timeout)
    return user_action