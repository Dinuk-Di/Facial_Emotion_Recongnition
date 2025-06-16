from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QSystemTrayIcon, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPixmap
from .styles import DASHBOARD_STYLE, CARD_STYLE, BUTTON_STYLE

class EmotionDashboard(QMainWindow):
    update_emotion = pyqtSignal(str, float)  # emotion, confidence
    update_agent = pyqtSignal(str, str)       # agent_name, message
    update_recommendation = pyqtSignal(str)   # recommendation
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emotion Assistant")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(DASHBOARD_STYLE)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        self.title = QLabel("Emotion Assistant")
        self.title.setFont(QFont("Arial", 24, QFont.Bold))
        self.title.setStyleSheet("color: #2c3e50;")
        header.addWidget(self.title)
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 24))
        self.status_indicator.setStyleSheet("color: #e74c3c;")
        header.addStretch()
        header.addWidget(QLabel("Status:"))
        header.addWidget(self.status_indicator)
        main_layout.addLayout(header)
        
        # Emotion card
        emotion_card = QWidget()
        emotion_card.setStyleSheet(CARD_STYLE)
        emotion_layout = QVBoxLayout(emotion_card)
        emotion_layout.setContentsMargins(20, 15, 20, 20)
        
        emotion_header = QLabel("Current Emotion")
        emotion_header.setFont(QFont("Arial", 16, QFont.Bold))
        emotion_layout.addWidget(emotion_header)
        
        # Emotion display
        self.emotion_display = QLabel("Neutral")
        self.emotion_display.setFont(QFont("Arial", 48, QFont.Bold))
        self.emotion_display.setAlignment(Qt.AlignCenter)
        emotion_layout.addWidget(self.emotion_display)
        
        # Confidence bar
        self.confidence_label = QLabel("Confidence: 0%")
        self.confidence_label.setFont(QFont("Arial", 12))
        emotion_layout.addWidget(self.confidence_label)
        
        main_layout.addWidget(emotion_card)
        
        # Agent activity
        agent_card = QWidget()
        agent_card.setStyleSheet(CARD_STYLE)
        agent_layout = QVBoxLayout(agent_card)
        agent_layout.setContentsMargins(20, 15, 20, 20)
        
        agent_header = QLabel("Agent Activity")
        agent_header.setFont(QFont("Arial", 16, QFont.Bold))
        agent_layout.addWidget(agent_header)
        
        # Agent log
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none; background: transparent;")
        
        self.agent_log = QWidget()
        self.agent_log_layout = QVBoxLayout(self.agent_log)
        self.agent_log_layout.setAlignment(Qt.AlignTop)
        self.agent_log_layout.setSpacing(10)
        
        scroll_area.setWidget(self.agent_log)
        agent_layout.addWidget(scroll_area)
        main_layout.addWidget(agent_card)
        
        # Recommendation card
        self.recommendation_card = QWidget()
        self.recommendation_card.setStyleSheet(CARD_STYLE)
        self.recommendation_card.hide()
        rec_layout = QVBoxLayout(self.recommendation_card)
        rec_layout.setContentsMargins(20, 15, 20, 20)
        
        rec_header = QLabel("Recommendation")
        rec_header.setFont(QFont("Arial", 16, QFont.Bold))
        rec_layout.addWidget(rec_header)
        
        self.recommendation_text = QLabel()
        self.recommendation_text.setFont(QFont("Arial", 14))
        self.recommendation_text.setWordWrap(True)
        rec_layout.addWidget(self.recommendation_text)
        
        self.execute_button = QPushButton("Execute")
        self.execute_button.setStyleSheet(BUTTON_STYLE)
        self.execute_button.setFixedHeight(40)
        rec_layout.addWidget(self.execute_button)
        
        main_layout.addWidget(self.recommendation_card)
        
        # Connect signals
        self.update_emotion.connect(self.update_emotion_display)
        self.update_agent.connect(self.log_agent_activity)
        self.update_recommendation.connect(self.show_recommendation)
        
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png"))
        self.tray_icon.activated.connect(self.toggle_window)
        
        # Status timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_indicator)
        self.status_timer.start(1000)
        self.status_counter = 0
        
    def toggle_window(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.setVisible(not self.isVisible())
    
    def update_status_indicator(self):
        self.status_counter = (self.status_counter + 1) % 4
        colors = ["#2ecc71", "#3498db", "#f39c12", "#e74c3c"]
        self.status_indicator.setStyleSheet(f"color: {colors[self.status_counter]};")
    
    def update_emotion_display(self, emotion, confidence):
        color_map = {
            "Happy": "#2ecc71",
            "Neutral": "#3498db",
            "Sad": "#9b59b6",
            "Angry": "#e74c3c",
            "Fear": "#f39c12",
            "Disgust": "#16a085",
            "Surprise": "#d35400",
            "Stress": "#c0392b",
            "Boring": "#7f8c8d"
        }
        
        color = color_map.get(emotion, "#3498db")
        self.emotion_display.setText(emotion)
        self.emotion_display.setStyleSheet(f"color: {color};")
        self.confidence_label.setText(f"Confidence: {confidence:.0f}%")
    
    def log_agent_activity(self, agent_name, message):
        timestamp = QApplication.instance().time.toString("hh:mm:ss")
        agent_label = QLabel(f"<b>[{timestamp}] {agent_name}:</b> {message}")
        agent_label.setWordWrap(True)
        agent_label.setStyleSheet("font-size: 12px; padding: 5px;")
        self.agent_log_layout.addWidget(agent_label)
        
        # Auto-scroll to bottom
        scrollbar = self.agent_log.parent().verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def show_recommendation(self, recommendation):
        if "No action" in recommendation:
            self.recommendation_card.hide()
            return
            
        self.recommendation_text.setText(recommendation)
        self.recommendation_card.show()
        self.execute_button.clicked.connect(
            lambda: QApplication.instance().execute_recommendation(recommendation)
        )
    
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Emotion Assistant",
            "The application is still running in the system tray",
            QSystemTrayIcon.Information,
            3000
        )

    def add_placeholder_logs(self):
        self.log_agent_activity("System", "Application started")
        self.log_agent_activity("Face Detection", "Webcam initialized")
        self.log_agent_activity("AI System", "Models loaded successfully")