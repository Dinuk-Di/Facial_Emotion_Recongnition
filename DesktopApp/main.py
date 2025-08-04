from tkinter import Tk
from customtkinter import CTk
from ui.login import LoginWindow
from database.db import get_connection

if __name__ == "__main__":
    # root = CTk()
    # app = LoginWindow(root)
    # root.mainloop()
    # get username and sessionid from database of user
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, session_id FROM users WHERE id = 1")  # Example query
    user_data = cursor.fetchone()
    username = None
    session_id = None
    if user_data:
        username, session_id = user_data
        print(f"Username: {username}, Session ID: {session_id}")
    else:
        print("User not found.")
    
    #open dashboard if username and session_id are found
    if username and session_id:
        app = CTk()
        app.title(f"Welcome, {username}")
        app.geometry("700x600")
        app.resizable(False, False)
        
        # Initialize the dashboard with the username
        from ui.dashboard import open_dashboard
        open_dashboard(username)
        
        app.mainloop()
    else:
        # open register window if user not found
        from ui.register import RegisterWindow
        root = CTk()
        app = RegisterWindow(root)
        root.mainloop()
        
