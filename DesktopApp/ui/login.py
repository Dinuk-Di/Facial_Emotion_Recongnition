import customtkinter as ctk
from tkinter import messagebox
from database.db import get_connection
from ui.dashboard import open_dashboard

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Login")
        self.position_bottom_right()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        frame = ctk.CTkFrame(root, corner_radius=10)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(frame, text="Login", font=("Arial", 20, "bold")).pack(pady=10)

        ctk.CTkLabel(frame, text="Username").pack()
        self.username_entry = ctk.CTkEntry(frame)
        self.username_entry.pack(pady=5)

        ctk.CTkLabel(frame, text="Password").pack()
        self.password_entry = ctk.CTkEntry(frame, show="*")
        self.password_entry.pack(pady=5)

        ctk.CTkButton(frame, text="Login", command=self.login).pack(pady=10)
        ctk.CTkButton(frame, text="Register", command=self.register).pack()

    def position_bottom_right(self):
        self.root.update_idletasks()
        width = 350
        height = 450
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - width - 10
        y = screen_height - height - 60
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        conn.close()

        if len(users) == 1:
            self.root.destroy()
            open_dashboard(users[0][1])
            return

        for user in users:
            if user[1] == username:
                self.root.destroy()
                open_dashboard(username)
                return

        messagebox.showerror("Login Failed", "Invalid username or password.")

    def register(self):
        from ui.register import RegisterWindow
        self.root.destroy()
        root = ctk.CTk()  # Also use CTk here!
        RegisterWindow(root)
        root.mainloop()
