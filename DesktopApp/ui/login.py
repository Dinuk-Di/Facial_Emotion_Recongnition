# ui/login.py
import tkinter as tk
from tkinter import messagebox
from database.db import get_connection
from ui.dashboard import open_dashboard

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Login")
        self.root.geometry("300x200")

        tk.Label(root, text="Username").pack()
        self.username_entry = tk.Entry(root)
        self.username_entry.pack()

        tk.Label(root, text="Password").pack()
        self.password_entry = tk.Entry(root, show="*")
        self.password_entry.pack()

        tk.Button(root, text="Login", command=self.login).pack(pady=10)
        tk.Button(root, text="Register", command=self.register).pack()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            self.root.destroy()
            open_dashboard(username)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def register(self):
        from ui.register import RegisterWindow
        self.root.destroy()
        root = tk.Tk()
        RegisterWindow(root)
        root.mainloop()
