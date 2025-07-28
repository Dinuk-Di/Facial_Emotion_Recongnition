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

        # Fetch all users
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        conn.close()

        if len(users) == 1:
            # Only one user exists, auto-login with that user's username
            print("[INFO] Only one user found. Logging in automatically.")
            self.root.destroy()
            open_dashboard(users[0][1])  # assuming column 1 is username
            return

        # Otherwise, match by entered credentials
        for user in users:
            if user[1] == username and user[2] == password:  # assuming [1]=username, [2]=password
                self.root.destroy()
                open_dashboard(username)
                return

        messagebox.showerror("Login Failed", "Invalid username or password.")


    def register(self):
        from ui.register import RegisterWindow
        self.root.destroy()
        root = tk.Tk()
        RegisterWindow(root)
        root.mainloop()
