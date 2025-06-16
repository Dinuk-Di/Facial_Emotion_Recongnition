from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

class AgentStatusUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agent Status")
        self.setFixedSize(300, 150)
        layout = QVBoxLayout()
        self.label_emotion = QLabel("Last Emotion: N/A")
        self.label_recommendation = QLabel("Recommendation: N/A")
        self.label_executed = QLabel("Executed: N/A")
        for lbl in [self.label_emotion, self.label_recommendation, self.label_executed]:
            layout.addWidget(lbl)
        self.setLayout(layout)

    def update_status(self, emotion, recommendation, executed):
        self.label_emotion.setText(f"Last Emotion: {emotion}")
        self.label_recommendation.setText(f"Recommendation: {recommendation}")
        self.label_executed.setText(f"Executed: {executed}")
