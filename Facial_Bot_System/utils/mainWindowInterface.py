# -*- coding: utf-8 -*-

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget, QPushButton)

class ClickableFrame(QFrame):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.normal_color = "rgba(85, 255, 255, 128)"
        self.hover_color = "rgba(100, 255, 255, 180)"  # Slightly brighter/lighter
        self.pressed_color = "rgba(70, 220, 220, 200)"  # Darker when pressed
        
        self.setStyleSheet(f"""
            ClickableFrame {{
                background-color: {self.normal_color};
                border-radius: 15px;
                border: 2px solid rgb(0, 255, 255);
            }}
        """)

    def enterEvent(self, event):
        self.setStyleSheet(f"""
            ClickableFrame {{
                background-color: {self.hover_color};
                border-radius: 15px;
                border: 2px solid rgb(0, 255, 255);
            }}
        """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.setStyleSheet(f"""
            ClickableFrame {{
                background-color: {self.normal_color};
                border-radius: 15px;
                border: 2px solid rgb(0, 255, 255);
            }}
        """)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setStyleSheet(f"""
                ClickableFrame {{
                    background-color: {self.pressed_color};
                    border-radius: 15px;
                    border: 2px solid rgb(0, 200, 200);
                }}
            """)
            self.clicked.emit()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setStyleSheet(f"""
            ClickableFrame {{
                background-color: {self.hover_color};
                border-radius: 15px;
                border: 2px solid rgb(0, 255, 255);
            }}
        """)
        super().mouseReleaseEvent(event)

class InteraceMainwindow(object):

    def add_choice(self, text="New Choice", id=None, icon_path=None, on_click=None):
        """Improved version with proper parameter usage"""
        choice_frame = ClickableFrame()
        choice_frame.setObjectName(text.replace(" ", "_"))  # Sanitize object name
        choice_frame.setMinimumSize(QSize(380, 60))
        choice_frame.setMaximumSize(QSize(380, 60))
        
        # Set style with proper selector
        choice_frame.setStyleSheet(f"""
        #{choice_frame.objectName()} {{
            background-color: rgba(85, 255, 255, 128);
            border-radius: 15px;
            border: 2px solid rgb(0, 255, 255);
        }}
        """)
        
        layout = QHBoxLayout(choice_frame)
        layout.setContentsMargins(5, 5, 5, 5)

        # Icon frame
        icon_frame = QFrame()
        icon_frame.setObjectName("ChoiceIcon")
        icon_frame.setFixedSize(QSize(60, 50))
        
        if icon_path:
            icon_frame.setStyleSheet(f"""
            #ChoiceIcon {{
                background-image: url({icon_path});
                background-position: center;
                background-repeat: no-repeat;
                border-radius: 15px;
            }}
            """)
        
        layout.addWidget(icon_frame)

        # Text frame
        text_frame = QFrame()
        text_label = QLabel(text)
        text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        text_label.setFont(QFont("Sans Serif", 11, QFont.Bold))
        
        text_layout = QVBoxLayout(text_frame)
        text_layout.addWidget(text_label)
        layout.addWidget(text_frame)

        # Connect click signal if provided
        if callable(on_click):
            choice_frame.clicked.connect(lambda: on_click(text,id))

        self.verticalLayout.addWidget(choice_frame)

    def setupUi(self, MainWindow):
        # ===== Main Window Setup =====
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(530, 240)
        MainWindow.setMinimumSize(QSize(527, 235))
        MainWindow.setMaximumSize(QSize(530, 240))
        MainWindow.setLayoutDirection(Qt.LeftToRight)

        # ===== Stylesheet =====
        MainWindow.setStyleSheet(u"""
        * {
            border: none;
            background-color: transparent;
            background: none;
            padding: 0;
            margin: 0;
        }                

        #ChoiceFrame {
            background-color: rgba(72, 170, 173, 255);
            border-radius: 15px;
        }

        #Icon {
            background-color: rgb(176, 176, 0);
            border-image: url(utils/res/Icon.jpg);
            border-radius: 15px;
        }
                                 
        #Close_Btn {
	        border-radius: 15px;
        }
        """)

        # ===== Central Widget =====
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")

        # ===== Main Frame =====
        self.MainFrame = QFrame(self.centralwidget)
        self.MainFrame.setObjectName(u"MainFrame")
        self.MainFrame.setGeometry(QRect(9, 9, 511, 221))
        self.MainFrame.setMinimumSize(QSize(511, 221))
        self.MainFrame.setMaximumSize(QSize(511, 221))
        self.MainFrame.setFrameShape(QFrame.StyledPanel)
        self.MainFrame.setFrameShadow(QFrame.Raised)

        # ===== Exit button =====
        self.Close_Btn = QPushButton(self.MainFrame)
        self.Close_Btn.setObjectName(u"Close_Btn")

        self.Close_Btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 30);
                border-radius: 3px;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 50);
            }
        """)

        self.Close_Btn.setEnabled(True)
        self.Close_Btn.setGeometry(QRect(10, 30, 31, 21))
        self.Close_Btn.setAutoFillBackground(False)
        icon = QIcon()
        icon.addFile(u"res/close.png", QSize(), QIcon.Normal, QIcon.Off)
        self.Close_Btn.setIcon(icon)
        self.Close_Btn.raise_()

        # ===== Icon Frame =====
        self.Icon = QFrame(self.MainFrame)
        self.Icon.setObjectName(u"Icon")
        self.Icon.setGeometry(QRect(410, 0, 100, 100))
        self.Icon.setMinimumSize(QSize(100, 100))
        self.Icon.setBaseSize(QSize(100, 100))
        self.Icon.setFrameShape(QFrame.Box)
        self.Icon.setFrameShadow(QFrame.Raised)

        # ===== Choice Frame =====
        self.ChoiceFrame = QFrame(self.MainFrame)
        self.ChoiceFrame.setObjectName(u"ChoiceFrame")
        self.ChoiceFrame.setGeometry(QRect(10, 49, 421, 162))
        self.ChoiceFrame.setMinimumSize(QSize(421, 161))
        self.ChoiceFrame.setLayoutDirection(Qt.LeftToRight)
        self.ChoiceFrame.setFrameShape(QFrame.StyledPanel)
        self.ChoiceFrame.setFrameShadow(QFrame.Raised)

        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        self.ChoiceFrame.setSizePolicy(sizePolicy)

        self.verticalLayout = QVBoxLayout(self.ChoiceFrame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSpacing(9)
        self.verticalLayout.setContentsMargins(15, 18, 26, 15)

        # frame_1 = add_choice("Watch Something New", "youtube_resize.png")
        # self.verticalLayout.addWidget(frame_1)

        # frame_2 = add_choice("Watch Something New", "youtube_resize.png")
        # self.verticalLayout.addWidget(frame_2)

        # Raise elements
        self.ChoiceFrame.raise_()
        self.Icon.raise_()

        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))

    pass