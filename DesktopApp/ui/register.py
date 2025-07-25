# ui/register.py
import tkinter as tk
from tkinter import messagebox
from database.db import get_connection
from ui.login import LoginWindow

class RegisterWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Register")
        self.root.geometry("300x300")

        tk.Label(root, text="Username").pack()
        self.username_entry = tk.Entry(root)
        self.username_entry.pack()

        tk.Label(root, text="Password").pack()
        self.password_entry = tk.Entry(root, show="*")
        self.password_entry.pack()

        tk.Button(root, text="Register", command=self.register_user).pack(pady=10)

    def register_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        conn = get_connection()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            messagebox.showinfo("Success", "Registration successful!")
            self.root.destroy()
            root = tk.Tk()
            LoginWindow(root)
            root.mainloop()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            conn.close()
