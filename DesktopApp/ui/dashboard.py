import tkinter as tk
from core.controller import AppController
from database.db import get_connection

controller = None

def open_dashboard(username):
    global controller
    root = tk.Tk()
    root.title(f"Welcome, {username}")
    root.geometry("400x300")

    tk.Label(root, text=f"Logged in as: {username}", font=("Arial", 14)).pack(pady=10)

    tk.Button(root, text="Start Monitoring", command=lambda: controller.start()).pack(pady=10)
    tk.Button(root, text="Stop Monitoring", command=lambda: controller.stop()).pack()
    tk.Button(root, text="Exit", command=root.destroy).pack(pady=20)

    controller = AppController()
    root.mainloop()
