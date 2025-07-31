import customtkinter as ctk
from tkinter import filedialog, messagebox
import winreg
from database.db import get_connection, add_app_data

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AppRegister:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        
        self.root.title("Apps Settings")
        self.root.geometry("650x800")

        self.emotions = ["Happy", "Neutral", "Fear", "Sad", "Angry", "Boaring", "Stress", "Disgust", "Suprise"]
        self.categories = ["Songs", "Entertainment", "SocialMedia", "Games", "Communication", "Help", "Other"]
        self.category_data = {}

        self.main_frame = ctk.CTkScrollableFrame(self.root, corner_radius=10)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(self.main_frame, text="Configure Your Applications", font=("Arial", 20, "bold")).pack(pady=10)
        for category in self.categories:
            self.add_category_block(category)

        ctk.CTkLabel(self.main_frame, text="How frequently do you need suggestions?",
                     font=("Arial", 14, "bold")).pack(pady=(20, 5))

        self.frequency = ctk.StringVar(value="Daily")
        freq_frame = ctk.CTkFrame(self.main_frame)
        freq_frame.pack(pady=5)

        for option in ["Hourly", "Daily", "Weekly"]:
            ctk.CTkRadioButton(freq_frame, text=option, variable=self.frequency, value=option).pack(side="left", padx=10)

        ctk.CTkButton(self.main_frame, text="Submit", command=self.submit).pack(pady=20)

    def add_category_block(self, category):
        block = ctk.CTkFrame(self.main_frame, border_width=1, corner_radius=10)
        block.pack(pady=10, fill="x", padx=5)

        ctk.CTkLabel(block, text=category, font=("Arial", 16, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

        self.category_data[category] = {"apps": []}

        self.update_app_list(category, block)

        add_button = ctk.CTkButton(block, text="+", width=30, height=30, corner_radius=15,
                                   font=("Arial", 20, "bold"),
                                   command=lambda c=category: self.open_add_app_popup(c, block))
        add_button.pack(pady=10)

    def update_app_list(self, category, parent_frame):
        if "app_labels" in self.category_data[category]:
            for label in self.category_data[category]["app_labels"]:
                label.destroy()

        self.category_data[category]["app_labels"] = []

        for name, _, _ in self.category_data[category]["apps"]:
            label = ctk.CTkLabel(parent_frame, text=f"\u2022 {name}", anchor="w")
            label.pack(anchor="w", padx=20)
            self.category_data[category]["app_labels"].append(label)

    def open_add_app_popup(self, category, parent_frame):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Add Application")
        popup.geometry("400x450")
        popup.resizable(False, False)

        ctk.CTkLabel(popup, text=f"Add App to '{category}'", font=("Arial", 16, "bold")).pack(pady=10)

        # App Name Entry
        ctk.CTkLabel(popup, text="App Name:").pack(anchor="w", padx=20)
        name_frame = ctk.CTkFrame(popup)
        name_frame.pack(pady=5)

        name_entry = ctk.CTkEntry(name_frame, width=240)
        name_entry.pack(side="left", padx=(0, 5))

        def search_installed_apps():
            name = name_entry.get().lower()
            matches = [app for app in self.get_installed_programs() if name in app[0].lower()]
            if matches:
                location_entry.delete(0, "end")
                location_entry.insert(0, matches[0][1])
            else:
                messagebox.showinfo("Not Found", "App not found. Please enter path manually.")

        search_btn = ctk.CTkButton(name_frame, text="🔍", width=40, command=search_installed_apps)
        search_btn.pack(side="left")

        # App Location Entry
        ctk.CTkLabel(popup, text="App Location:").pack(anchor="w", padx=20)
        location_frame = ctk.CTkFrame(popup)
        location_frame.pack(pady=5)

        location_entry = ctk.CTkEntry(location_frame, width=240)
        location_entry.pack(side="left", padx=(0, 5))

        def browse_file():
            path = filedialog.askopenfilename()
            if path:
                location_entry.delete(0, "end")
                location_entry.insert(0, path)

        browse_btn = ctk.CTkButton(location_frame, text="📁", width=40, command=browse_file)
        browse_btn.pack(side="left")

        # Emotion Selection (Scrollable)
        ctk.CTkLabel(popup, text="Select Emotions:").pack(anchor="w", padx=20, pady=(10, 0))

        emotion_scroll_container = ctk.CTkFrame(popup)
        emotion_scroll_container.pack(padx=20, pady=5, fill="x")

        emotion_scroll_frame = ctk.CTkScrollableFrame(
            emotion_scroll_container,
            orientation="horizontal",
            height=60,
            corner_radius=5,
            fg_color="transparent"
        )
        emotion_scroll_frame.pack(fill="x", expand=True)

        emotion_vars = []
        for emo in self.emotions:
            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(emotion_scroll_frame, text=emo, variable=var)
            cb.pack(side="left", padx=5)
            emotion_vars.append((emo, var))

    # Save App Button
        def save_app():
            name = name_entry.get()
            path_val = location_entry.get()
            selected_emotions = [emo for emo, var in emotion_vars if var.get()]

            if not name or not selected_emotions:
                messagebox.showwarning("Missing", "Please enter app name and select at least one emotion.")
                return

            is_local = bool(path_val)
            app_url = None

            self.category_data[category]["apps"].append((name, path_val, selected_emotions))
            conn = get_connection()

            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE username = ?", (self.username,))
                user_id = cursor.fetchone()[0]

                add_app_data(
                    conn=conn,
                    user_id=user_id,
                    category=category,
                    app_name=name,
                    app_url=app_url,
                    path=path_val,
                    is_local=is_local,
                    selected_emotions=selected_emotions
                )

                messagebox.showinfo("Success", "App added successfully.")
                popup.destroy()
                self.update_app_list(category, parent_frame)

            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to add app: {e}")
                print(f"[DB Error] {e}")

        ctk.CTkButton(popup, text="Add", command=save_app).pack(pady=15)



    def get_installed_programs(self):
        uninstall_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        program_paths = []
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(root, uninstall_key) as key:
                        for i in range(0, winreg.QueryInfoKey(key)[0]):
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                    program_paths.append((display_name, install_location))
                                except FileNotFoundError:
                                    continue
            except FileNotFoundError:
                    continue
        return program_paths

    def submit(self):
        collected_data = {}
        for category in self.categories:
            apps = self.category_data[category]["apps"]
            collected_data[category] = {"apps": apps}
        suggestion_freq = self.frequency.get()
        print("Collected Data:", collected_data)
        print("Suggestion Frequency:", suggestion_freq)
        messagebox.showinfo("Submitted", "Your preferences have been saved!")




# # with out database add
        # def save_app():
        #     name = name_entry.get()
        #     path = location_entry.get()
        #     selected_emotions = [emo for emo, var in emotion_vars if var.get()]
        #     if not name or not path or not selected_emotions:
        #         messagebox.showwarning("Missing", "Fill in all fields and select at least one emotion.")
        #         return
        #     self.category_data[category]["apps"].append((name, path, selected_emotions))
        #     popup.destroy()
        #     self.update_app_list(category, parent_frame)