
import customtkinter as ctk
from tkinter import messagebox
from database.db import initialize_db
from ui.app_register import AppRegister
import uuid

class RegisterWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("EMOFI - Register")
        self.position_bottom_right()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        frame = ctk.CTkFrame(root, corner_radius=15)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(frame, text="Register", font=("Arial", 24, "bold")).pack(pady=(20, 10))

        # Username
        ctk.CTkLabel(frame, text="Username").pack()
        self.username_entry = ctk.CTkEntry(frame, width=220, height=35, placeholder_text="Enter username")
        self.username_entry.pack(pady=(5, 10))

        # Phone Number
        ctk.CTkLabel(frame, text="Phone Number").pack()
        self.phone_entry = ctk.CTkEntry(frame, width=220, height=35, placeholder_text="Enter phone number")
        self.phone_entry.pack(pady=(5, 10))

        # Birthday
        ctk.CTkLabel(frame, text="Birthday (YYYY-MM-DD)").pack()
        self.birthday_entry = ctk.CTkEntry(frame, width=220, height=35, placeholder_text="YYYY-MM-DD")
        self.birthday_entry.pack(pady=(5, 15))

        # Next Button
        ctk.CTkButton(frame, text="Next", width=220, height=40, corner_radius=8, command=self.register_and_continue).pack(pady=15)

    def position_bottom_right(self):
        self.root.update_idletasks()
        width = 400
        height = 450
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width -170
        y = screen_height - height - 20
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.resizable(False, False)

    def register_and_continue(self):
        username = self.username_entry.get()
        phone = self.phone_entry.get()
        birthday = self.birthday_entry.get()
        session_id = str(uuid.uuid4())

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

            self.root.destroy()
            root = ctk.CTk()
            AppRegister(root, username)
            root.mainloop()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            conn.close()
