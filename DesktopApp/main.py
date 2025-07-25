from tkinter import Tk
from ui.login import LoginWindow

if __name__ == "__main__":
    root = Tk()
    app = LoginWindow(root)
    root.mainloop()
