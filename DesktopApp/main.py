from tkinter import Tk
from customtkinter import CTk
from ui.login import LoginWindow

def start_app():
    root = CTk()
    app = LoginWindow(root)
    root.mainloop()

if __name__ == "__main__":
    root = CTk()
    app = LoginWindow(root)
    root.mainloop()
