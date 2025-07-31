# import customtkinter as ctk
# from tkinter import messagebox
# from database.db import get_connection
# from ui.login import LoginWindow

# class RegisterWindow:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("Register")
#         self.root.geometry("350x300")
#         self.position_bottom_right()

#         ctk.set_appearance_mode("dark")
#         ctk.set_default_color_theme("blue")

#         frame = ctk.CTkFrame(root, corner_radius=10)
#         frame.pack(padx=20, pady=20, fill="both", expand=True)

#         ctk.CTkLabel(frame, text="Register", font=("Arial", 20, "bold")).pack(pady=10)

#         ctk.CTkLabel(frame, text="Username").pack()
#         self.username_entry = ctk.CTkEntry(frame)
#         self.username_entry.pack(pady=5)

#         ctk.CTkLabel(frame, text="Password").pack()
#         self.password_entry = ctk.CTkEntry(frame, show="*")
#         self.password_entry.pack(pady=5)

#         ctk.CTkButton(frame, text="Register", command=self.register_user).pack(pady=10)

#     def position_bottom_right(self):
#         self.root.update_idletasks()
#         width = 350
#         height = 450
#         screen_width = self.root.winfo_screenwidth()
#         screen_height = self.root.winfo_screenheight()
#         x = screen_width - width - 10
#         y = screen_height - height - 60
#         self.root.geometry(f"{width}x{height}+{x}+{y}")

#     def register_user(self):
#         username = self.username_entry.get()
#         password = self.password_entry.get()

#         if not username or not password:
#             messagebox.showwarning("Warning", "Please fill in all fields.")
#             return

#         conn = get_connection()
#         try:
#             conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
#             conn.commit()
#             messagebox.showinfo("Success", "Registration successful!")
#             self.root.destroy()
#             root = ctk.CTk()
#             LoginWindow(root)
#             root.mainloop()
#         except Exception as e:
#             messagebox.showerror("Error", f"An error occurred: {e}")
#         finally:
#             conn.close()


import customtkinter as ctk
from tkinter import messagebox
from database.db import initialize_db
from ui.login import LoginWindow
import uuid
import subprocess  # To call app_register.py
import os
from ui.app_register import AppRegister

class RegisterWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Register")
        self.root.geometry("350x400")
        self.position_bottom_right()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        frame = ctk.CTkFrame(root, corner_radius=10)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(frame, text="Register", font=("Arial", 20, "bold")).pack(pady=10)

        ctk.CTkLabel(frame, text="Username").pack()
        self.username_entry = ctk.CTkEntry(frame)
        self.username_entry.pack(pady=5)

        ctk.CTkLabel(frame, text="Phone Number").pack()
        self.phone_entry = ctk.CTkEntry(frame)
        self.phone_entry.pack(pady=5)

        ctk.CTkLabel(frame, text="Birthday (YYYY-MM-DD)").pack()
        self.birthday_entry = ctk.CTkEntry(frame)
        self.birthday_entry.pack(pady=5)

        ctk.CTkButton(frame, text="Next", command=self.register_and_continue).pack(pady=15)

    def position_bottom_right(self):
        self.root.update_idletasks()
        width = 350
        height = 450
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - width - 10
        y = screen_height - height - 60
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def register_and_continue(self):
        username = self.username_entry.get()
        phone = self.phone_entry.get()
        birthday = self.birthday_entry.get()
        session_id = str(uuid.uuid4())  # Generate random session ID

        if not username or not phone or not birthday:
            messagebox.showwarning("Warning", "Please fill in all fields.")
            return

        conn = initialize_db()
        try:
            conn.execute(
                "INSERT INTO users (username, phonenumber, birthday, session_id) VALUES (?, ?, ?, ?)",
                (username, phone, birthday, session_id)
            )
            conn.commit()
            messagebox.showinfo("Success", "Registration successful!")

            # Close current window
            self.root.destroy()

            # Launch app_register.py
            root = ctk.CTk()
            AppRegister(root,username)
            root.mainloop()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            conn.close()
