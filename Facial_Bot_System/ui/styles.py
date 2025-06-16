DASHBOARD_STYLE = """
    QMainWindow {
        background-color: #f5f7fa;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    QLabel {
        color: #34495e;
    }
"""

CARD_STYLE = """
    QWidget {
        background-color: white;
        border-radius: 10px;
        padding: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
    }
"""

BUTTON_STYLE = """
    QPushButton {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
        padding: 8px 16px;
        font-weight: bold;
        border: none;
    }
    QPushButton:hover {
        background-color: #2980b9;
    }
    QPushButton:pressed {
        background-color: #1c6ea4;
    }
"""

AGENT_COLORS = {
    "Face Detection": "#3498db",
    "Emotion Analysis": "#9b59b6",
    "Task Detection": "#2ecc71",
    "Recommendation": "#f39c12",
    "Action": "#e74c3c"
}