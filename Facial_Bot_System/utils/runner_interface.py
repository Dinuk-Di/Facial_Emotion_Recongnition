import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
from Interface import Ui_MainWindow  # Your auto-generated class

class MainWindow(QMainWindow):
    def __init__(self, choices):
        super().__init__()
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.move(990, 580)

        for idx, choice in enumerate(choices):
            self.add_choice_main(choice['text'], "res/youtube_resize.png", on_click_choice)

        self.ui.Close_Btn.clicked.connect(self.close)

    def add_choice_main(self, text, icon_path= None, on_click = None):
        self.ui.add_choice(text, icon_path, on_click)

def launch_window(options):
    """Function to create and return the window instance"""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    window = MainWindow(choices=options)
    window.show()
    return window, app

def on_click_choice(text):
    print(f"Button Clicked {text}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.add_choice_main("Watch Something New", "res/youtube_resize.png", on_click_choice)
    window.add_choice_main("Listen to calming music", "res/spotify.png", on_click_choice)
    window.show()
    sys.exit(app.exec())
