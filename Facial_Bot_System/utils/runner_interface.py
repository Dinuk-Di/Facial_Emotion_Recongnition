import sys
from utils.mainWindowInterface import InteraceMainwindow
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt

Icons_paths = [
        {"app_name": "YouTube","icon_path": "utils/res/Youtube.png"},
        {"app_name": "Spotify","icon_path": "utils/res/Spotify.png"},
        {"app_name": "Discord","icon_path": "utils/res/Discord.png"},
        {"app_name": "Zoom","icon_path": "utils/res/Zoom.png"},
        {"app_name": "Microsoft Teams","icon_path": "utils/res/Teams.png"},
        {"app_name": "Skype","icon_path": "utils/res/Skype.png"},
        {"app_name": "Telegram Desktop","icon_path": "utils/res/Telegram.png"},
        {"app_name": "WhatsApp","icon_path": "utils/res/Whatsapp.png"},
        {"app_name": "Microsoft Solitaire Collection","icon_path": "utils/res/Solitaire.png"},
        {"app_name": "Default","icon_path": "utils/res/default_app.png"},
    ]

def setup_Icons(app_name, icon_paths):
    default_icon = "utils/res/default_app.png"
    icon_path = default_icon
    
    for idx, icon in enumerate(icon_paths):
        if app_name == icon['app_name']:
            icon_path = icon['icon_path']
            break
    return icon_path

class MainWindow(QMainWindow):
    def __init__(self, choices):
        super().__init__()
        self.selectedChoice = None
        self.allchoices = choices
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.ui = InteraceMainwindow()
        self.ui.setupUi(self)
        # Connect search callback
        self.ui.search_callback = self.handle_youtube_search
        self.move(990, 580)

        for idx, choice in enumerate(choices[0:2]):
            icon = setup_Icons(choice['app_name'], Icons_paths)
            self.add_choice_main(choice['text'], idx, icon, self.on_clicked_choice)
        self.ui.Close_Btn.clicked.connect(self.close)

    def add_choice_main(self, text, id=None, icon_path= None, on_click = None):
        self.ui.add_choice(text, id, icon_path, on_click)

    def on_clicked_choice(self, content, id):
        selected = self.allchoices[id]
        self.selectedChoice = selected
        self.ui.selected_choice = selected  # Store for default query
        
        if selected.get('app_name', '').lower() == 'youtube':
            self.ui.show_search()
            self.ui.search_input.setFocus()
            default_query = selected.get('search_query', '')
            self.ui.search_input.setPlaceholderText(f"e.g. {default_query}" if default_query else "Enter search query...")
        else:
            print(f"Selected: {id},{content}")
            self.close()

    
    def handle_youtube_search(self, query):
        if query is None:  # User cancelled
            return
            
        # Find the YouTube option
        youtube_choice = None
        for choice in self.allchoices:
            if choice.get('app_name', '').lower() == 'youtube':
                youtube_choice = choice
                break
                
        if youtube_choice:
            # Update the choice with the custom query
            youtube_choice['search_query'] = query
            self.selectedChoice = youtube_choice
            self.close()
    #def show_recommendations(self, show):

def launch_window(options):
    """Function to create and return the window instance"""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    window = MainWindow(choices=options)
    window.show()
    print("The content of choise selection output, window,apps: ", app, window)
    return window, app

if __name__ == "__main__":
    app = QApplication(sys.argv)

    options = [
        {'text': 'Watch relaxing video'},
        {'text': 'Watch funny video'}
    ]

    window = MainWindow(options)
    window.show()
    app.exec()
    print("Final choice: ", window.selectedChoice)
