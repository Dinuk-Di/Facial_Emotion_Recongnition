# from typing import List
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# import win32api
# import win32con
# import time
# import subprocess
# import webbrowser
# from win11toast import toast
# import os
# import threading
# icon_path = r'D:\RuhunaNew\Academic\Research\Facial_Recog_Repo\Group_50_Repo\DesktopApp\assets\res\Icon.jpg'
# executer_path = r'executer.pyw'
# import tkinter as tk
# import os
# import ctypes
# import tkinter as tk

# def send_notification(title, recommended_output, recommended_options, timeout=None):
#     selected_app = {"value": None}

#     def show_app_options(app_options):
#         for widget in frame.winfo_children():
#             widget.destroy()

#         tk.Label(frame, text="Choose an app:", bg="#2b2b2b", fg="white", font=("Segoe UI", 10)).pack(pady=(0, 10))

#         for option in app_options:
#             btn = tk.Button(frame, text=option.app_name, width=25, bg="#3c3f41", fg="white", font=("Segoe UI", 9),
#                             relief="flat", highlightthickness=0, command=lambda opt=option: handle_app_selection(opt))
#             btn.pack(pady=3)

#     def handle_app_selection(option):
#         # If local app, select immediately
#         if option.is_local:
#             select_app(option, None)
#         else:
#             # Show input field for search query
#             show_search_input(option)

#     def show_search_input(option):
#         for widget in frame.winfo_children():
#             widget.destroy()

#         tk.Label(frame, text=f"Enter search text for {option.app_name} (or skip):", bg="#2b2b2b", fg="white",
#                  font=("Segoe UI", 10), wraplength=280).pack(pady=(10, 5))

#         query_entry = tk.Entry(frame, width=25, font=("Segoe UI", 10))
#         query_entry.pack(pady=10)

#         btn_frame = tk.Frame(frame, bg="#2b2b2b")
#         btn_frame.pack(pady=10)

#         # Confirm with query
#         tk.Button(btn_frame, text="Search", bg="#3c3f41", fg="white", width=10,
#                   command=lambda: select_app(option, query_entry.get())).pack(side="left", padx=5)

#         # Skip query
#         tk.Button(btn_frame, text="Skip", bg="#3c3f41", fg="white", width=10,
#                   command=lambda: select_app(option, None)).pack(side="left", padx=5)

#     def select_app(option, custom_query):
#         selected_app["value"] = {
#             "app_name": option.app_name,
#             "app_url": option.app_url,
#             "search_query": custom_query if custom_query else option.search_query,
#             "is_local": option.is_local
#         }
#         root.destroy()

#     def select_recommendation(index):
#         show_app_options(recommended_options[index])

#     # Create main window
#     root = tk.Tk()
#     root.title(title)
#     root.overrideredirect(True)
#     root.attributes("-topmost", True)
#     root.configure(bg="#2b2b2b")

#     width, height = 320, 250
#     x = root.winfo_screenwidth() - width - 20
#     y = 50
#     root.geometry(f"{width}x{height}+{x}+{y}")

#     frame = tk.Frame(root, bg="#2b2b2b", bd=2)
#     frame.place(relwidth=1, relheight=1)

#     tk.Label(frame, text=title, bg="#2b2b2b", fg="white", font=("Segoe UI", 12, "bold")).pack(pady=(10, 5))
#     tk.Label(frame, text="Choose an option:", bg="#2b2b2b", fg="white", font=("Segoe UI", 10)).pack(pady=(0, 10))

#     for idx, rec in enumerate(recommended_output):
#         tk.Button(frame, text=rec, width=25, bg="#3c3f41", fg="white", font=("Segoe UI", 9),
#                   relief="flat", highlightthickness=0, command=lambda i=idx: select_recommendation(i)).pack(pady=3)

#     if timeout:
#         root.after(timeout, root.destroy)

#     root.mainloop()
#     return selected_app["value"]



# def execute_task(option):
#     time.sleep(5)
#     try:
#         app_name = option.get("app_name")
#         app_url = option.get("app_url")
#         search_query = option.get("search_query")

#         if app_url.startswith("http"):
#             if search_query:
#                 webbrowser.open(f"{app_url}/results?search_query={search_query}")
#             else:
#                 webbrowser.open(app_url)
#         elif "://" in app_url:
#             subprocess.Popen([app_url], shell=True)
#         else:
#             print(f"Unknown URL format: {app_url}")
#     except Exception as e:
#         print(f"[Execution Error] {e}")

import tkinter as tk
import webbrowser
import subprocess
import time

def send_notification(title, recommended_output, recommended_options, timeout=None):
    selected_app = {"value": None}

    def show_app_options(app_options):
        for widget in frame.winfo_children():
            widget.destroy()

        tk.Label(frame, text="Choose an app:", bg=BG_COLOR, fg="white", font=("Segoe UI", 10, "bold")).pack(pady=(0, 10))

        for option in app_options:
            btn = tk.Button(frame, text=option.app_name, width=25, bg=BTN_COLOR, fg="white", font=("Segoe UI", 9),
                            relief="flat", highlightthickness=0, bd=0, activebackground=HOVER_COLOR,
                            command=lambda opt=option: handle_app_selection(opt))
            btn.pack(pady=5)
            add_hover_effect(btn)

    def handle_app_selection(option):
        if option.is_local:
            select_app(option, None)
        else:
            show_search_input(option)

    def show_search_input(option):
        for widget in frame.winfo_children():
            widget.destroy()

        tk.Label(frame, text=f"Enter search text for {option.app_name}:", bg=BG_COLOR, fg="white",
                 font=("Segoe UI", 10), wraplength=280).pack(pady=(10, 5))

        query_entry = tk.Entry(frame, width=28, font=("Segoe UI", 10), relief="flat", highlightthickness=1,
                               highlightbackground="#555", highlightcolor="#888")
        query_entry.pack(pady=10)

        btn_frame = tk.Frame(frame, bg=BG_COLOR)
        btn_frame.pack(pady=10)

        search_btn = tk.Button(btn_frame, text="Search", bg=BTN_COLOR, fg="white", width=10,
                               command=lambda: select_app(option, query_entry.get()))
        skip_btn = tk.Button(btn_frame, text="Skip", bg=BTN_COLOR, fg="white", width=10,
                             command=lambda: select_app(option, None))

        search_btn.pack(side="left", padx=5)
        skip_btn.pack(side="left", padx=5)

        add_hover_effect(search_btn)
        add_hover_effect(skip_btn)

    def select_app(option, custom_query):
        selected_app["value"] = {
            "app_name": option.app_name,
            "app_url": option.app_url,
            "search_query": custom_query if custom_query else option.search_query,
            "is_local": option.is_local
        }
        root.destroy()

    def select_recommendation(index):
        show_app_options(recommended_options[index])

    def add_hover_effect(widget):
        def on_enter(e):
            widget.config(bg=HOVER_COLOR)
        def on_leave(e):
            widget.config(bg=BTN_COLOR)
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    # Colors
    BG_COLOR = "#2b2b2b"   # Background color
    BTN_COLOR = "#3c3f41"  # Button color
    HOVER_COLOR = "#505354" # Hover color

    # Create main window
    root = tk.Tk()
    root.title(title)
    root.overrideredirect(True)  # Remove window frame
    root.attributes("-topmost", True)
    root.configure(bg=BG_COLOR)

    # Window size and position (bottom-right)
    width, height = 340, 260
    x = root.winfo_screenwidth() - width - 20
    y = root.winfo_screenheight() - height - 60
    root.geometry(f"{width}x{height}+{x}+{y}")

    frame = tk.Frame(root, bg=BG_COLOR, bd=0)
    frame.place(relwidth=1, relheight=1)

    tk.Label(frame, text=title, bg=BG_COLOR, fg="white", font=("Segoe UI", 12, "bold")).pack(pady=(10, 5))
    tk.Label(frame, text="Choose an option:", bg=BG_COLOR, fg="white", font=("Segoe UI", 10)).pack(pady=(0, 10))

    for idx, rec in enumerate(recommended_output):
        btn = tk.Button(frame, text=rec, width=25, bg=BTN_COLOR, fg="white", font=("Segoe UI", 9),
                        relief="flat", highlightthickness=0, bd=0, activebackground=HOVER_COLOR,
                        command=lambda i=idx: select_recommendation(i))
        btn.pack(pady=5)
        add_hover_effect(btn)

    if timeout:
        root.after(timeout, root.destroy)

    root.mainloop()
    return selected_app["value"]


def execute_task(option):
    time.sleep(5)
    try:
        app_name = option.get("app_name")
        app_url = option.get("app_url")
        search_query = option.get("search_query")

        if app_url.startswith("http"):
            if search_query:
                webbrowser.open(f"{app_url}/results?search_query={search_query}")
            else:
                webbrowser.open(app_url)
        elif "://" in app_url:
            subprocess.Popen([app_url], shell=True)
        else:
            print(f"Unknown URL format: {app_url}")
    except Exception as e:
        print(f"[Execution Error] {e}")
