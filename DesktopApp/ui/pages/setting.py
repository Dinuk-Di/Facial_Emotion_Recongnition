import customtkinter as ctk

class SettingsPage:
    def __init__(self, parent):
        # Main frame
        self.frame = ctk.CTkFrame(parent, fg_color="#1a1a1a")
        self.frame.pack(fill="both", expand=True)

        # Title
        title_label = ctk.CTkLabel(self.frame, text="Settings Page", font=("Arial", 20, "bold"), text_color="white")
        title_label.pack(pady=(30, 20))

        # Focus Time Label and Entry
        focus_label = ctk.CTkLabel(self.frame, text="Focus Time (seconds):", font=("Arial", 14), text_color="white")
        focus_label.pack(pady=(10, 5))

        self.focus_time_entry = ctk.CTkEntry(self.frame, placeholder_text="Enter focus time in seconds", width=250)
        self.focus_time_entry.pack(pady=5)

        # Monitoring Time Label and Entry
        monitor_label = ctk.CTkLabel(self.frame, text="Monitoring Time (seconds):", font=("Arial", 14), text_color="white")
        monitor_label.pack(pady=(15, 5))

        self.monitor_time_entry = ctk.CTkEntry(self.frame, placeholder_text="Enter monitoring time in seconds", width=250)
        self.monitor_time_entry.pack(pady=5)

        # Update Button
        update_button = ctk.CTkButton(self.frame, text="Update Settings", command=self.update_settings)
        update_button.pack(pady=(25, 10))

        # Feedback Label
        self.feedback_label = ctk.CTkLabel(self.frame, text="", text_color="lightgreen", font=("Arial", 12))
        self.feedback_label.pack(pady=10)

    def update_settings(self):
        try:
            focus_time = int(self.focus_time_entry.get())
            monitor_time = int(self.monitor_time_entry.get())

            # Validate positive integers
            if focus_time <= 0 or monitor_time <= 0:
                self.feedback_label.configure(text="Please enter positive numbers.", text_color="red")
                return

            # Save or use these values in your app logic
            self.feedback_label.configure(text=f"Settings updated! Focus: {focus_time}s, Monitor: {monitor_time}s", text_color="lightgreen")

            # TODO: Save these values in a config or pass to agent logic
            print(f"[Settings] Focus Time: {focus_time}, Monitoring Time: {monitor_time}")

        except ValueError:
            self.feedback_label.configure(text="Invalid input! Enter numbers only.", text_color="red")
