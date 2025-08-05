import customtkinter as ctk
from tkinter import filedialog, messagebox
import winreg
from database.db import get_connection, add_app_data
import os
from PIL import Image, ImageDraw
from ui.dashboard import open_dashboard

ASSET_PATH = "assets/res"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AppRegister:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        
        self.root.title("Apps Settings")
        self.position_bottom_right()
     

        self.categories = ["Songs", "Entertainment", "SocialMedia", "Games", "Communication", "Help", "Other"]
        self.category_data = {}

        self.main_frame = ctk.CTkScrollableFrame(self.root, corner_radius=10)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        self.build_ui()

    def position_bottom_right(self):
            self.root.update_idletasks()
            width = 350
            height = 450
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = screen_width - 100
            y = screen_height - height - 20
            self.root.geometry(f"{width}x{height}+{x}+{y}")
            self.root.resizable(False, False)

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

        header_frame = ctk.CTkFrame(block, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(header_frame, text=category, font=("Arial", 16, "bold")).pack(side="left")

        add_button = ctk.CTkButton(header_frame, text="+", width=30, height=30, corner_radius=15,
                                font=("Arial", 20, "bold"),
                                command=lambda c=category: self.open_add_app_popup(c, block))
        add_button.pack(side="left", padx=(10, 0))

        # Horizontal container for app icons
        app_icon_frame = ctk.CTkFrame(block, fg_color="transparent")
        app_icon_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.category_data[category] = {
            "apps": [],
            "app_icon_frame": app_icon_frame,
            "app_widgets": []
        }
    
    def load_app_icon(self, app_name):
        filename = f"{app_name.lower().replace(' ', '')}.png"
        path = os.path.join(ASSET_PATH, filename)
        fallback_path = os.path.join(ASSET_PATH, "Other.png")

        try:
            img = Image.open(path)
        except FileNotFoundError:
            img = Image.open(fallback_path)

        img = img.resize((50, 50)).convert("RGBA")
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
        img.putalpha(mask)
        return ctk.CTkImage(light_image=img, size=(50, 50))

    def confirm_delete_app(self, category, index, parent_frame):
        confirm = messagebox.askyesno("Delete App", "Are you sure you want to remove this app?")
        if confirm:
            del self.category_data[category]["apps"][index]
            self.update_app_list(category, parent_frame)


    def update_app_list(self, category, parent_frame):
        # Clear existing widgets
        for widget in self.category_data[category]["app_widgets"]:
            widget.destroy()
        self.category_data[category]["app_widgets"] = []

        frame = self.category_data[category]["app_icon_frame"]

        for index, (name, path_val,) in enumerate(self.category_data[category]["apps"]):
            icon_image = self.load_app_icon(name)

            app_frame = ctk.CTkFrame(frame, fg_color="transparent", width=80, height=100)
            app_frame.pack(side="left", padx=8, pady=5)

            # Icon container to position delete button over it
            icon_container = ctk.CTkFrame(app_frame, fg_color="transparent", width=60, height=60)
            icon_container.pack()
            icon_container.pack_propagate(False)

            icon_label = ctk.CTkLabel(icon_container, text="", image=icon_image)
            icon_label.image = icon_image
            icon_label.pack()

            # Position tiny delete button bottom right inside icon_container
            delete_btn = ctk.CTkButton(
                icon_container,
                text="✖",
                width=15,
                height=15,
                fg_color="red",
                hover_color="#aa0000",
                font=("Arial", 10),
                command=lambda idx=index: self.confirm_delete_app(category, idx, parent_frame)
            )
            delete_btn.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-2)

            name_label = ctk.CTkLabel(app_frame, text=name, font=("Arial", 10), wraplength=70)
            name_label.pack(pady=(4, 0))

            self.category_data[category]["app_widgets"].append(app_frame)




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

        # def search_installed_apps():
        #     name = name_entry.get().lower()
        #     matches = [app for app in self.get_installed_programs() if name in app[0].lower()]
        #     if matches:
        #         location_entry.delete(0, "end")
        #         location_entry.insert(0, matches[0][1])
        #     else:
        #         messagebox.showinfo("Not Found", "App not found. Please enter path manually.")

        def search_installed_apps():
            name = name_entry.get().lower()
            matches = [app for app in self.get_installed_programs() if name in app[0].lower()]
            if matches:
                install_location = matches[0][1]
                exe_path = find_executable_in_folder(install_location)
                location_entry.delete(0, "end")
                if exe_path:
                    location_entry.insert(0, exe_path)
                else:
                    location_entry.insert(0, install_location)  # fallback to folder
                    messagebox.showinfo("Executable Not Found", "App found, but .exe file not located.")
            else:
                messagebox.showinfo("Not Found", "App not found. Please enter path manually.")

        def find_executable_in_folder(folder_path):
            if not os.path.isdir(folder_path):
                return None

            exe_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(".exe"):
                        exe_files.append(os.path.join(root, file))

            # Optionally: filter or rank executables to find the main one
            if exe_files:
                # Example: return the shortest path or the one that matches folder name
                exe_files.sort(key=lambda x: len(x))  # heuristic: shortest path = most likely
                return exe_files[0]

            return None

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

        

    # Save App Button
        def save_app():
            name = name_entry.get()
            path_val = location_entry.get()
            # selected_emotions = [emo for emo, var in emotion_vars if var.get()]

            if not name:
                messagebox.showwarning("Missing", "Please enter app name")
                return

            is_local = bool(path_val)
            app_url = None

            self.category_data[category]["apps"].append((name, path_val))
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
                    is_local=is_local
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
        self.root.destroy()
        open_dashboard(self.username)



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