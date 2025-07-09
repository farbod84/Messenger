import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton,
                               QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QTextEdit,
                               QCheckBox, QLineEdit, QFileDialog, QFrame, QListWidget,
                               QTextBrowser, QFormLayout, QDialog)
from PySide6.QtGui import QFont, QPainter, QPixmap, QRegularExpressionValidator
from PySide6.QtCore import Qt, QRegularExpression, QTimer


MAX_WIDTH = 400

class Application(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        font = QFont("Georgia", 32)
        self.setFont(font)

        self.setStyleSheet("""
                    QWidget {
                        background-color: #f2f2f2;
                    }

                    QLabel {
                        background: transparent;
                        font-size: 24px;
                        color: #333;
                    }

                    QLineEdit {
                        color: black;
                        border: 2px solid #ccc;
                        border-radius: 8px;
                        padding: 10px;
                        font-size: 24px;
                        background-color: white;
                    }
                    
                    QLineEdit:placeholder {
                        color: gray;
                    }

                    QPushButton {
                        background-color: #0078D7;
                        color: white;
                        border: none;
                        padding: 10px;
                        font-size: 24px;
                        border-radius: 8px;
                    }

                    QPushButton:hover {
                        background-color: #005a9e;
                    }

                    QCheckBox {
                        background-color: transparent;
                        font-size: 24px;
                        color: white;
                    }
        """)


app = Application(sys.argv)


class Widget(QWidget):
    def __init__(self, title = None):
        super().__init__()

        self.setWindowTitle(title)
        self.setGeometry(350, 100, 1920, 1200)

    def paintEvent(self, event):
        painter = QPainter(self)
        pixmap = QPixmap("background_image.jpg")
        painter.drawPixmap(self.rect(), pixmap)
        super().paintEvent(event)

class Label(QLabel):
    def __init__(self, text = None):
        super().__init__()

        self.setText(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMaximumWidth(MAX_WIDTH)

class HBoxLayout(QHBoxLayout):
    def __init__(self):
        super().__init__()

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

class VBoxLayout(QVBoxLayout):
    def __init__(self):
        super().__init__()

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

class LineEdit(QLineEdit):
    def __init__(self, place_holder_text = None, is_password = False):
        super().__init__()

        self.setPlaceholderText(place_holder_text)
        self.setMaximumWidth(MAX_WIDTH)
        if is_password:
            self.setEchoMode(QLineEdit.Password)

    def set_password_visibility(self, state):
        if state == 2:
            self.setEchoMode(QLineEdit.Normal)
        else:
            self.setEchoMode(QLineEdit.Password)

class CheckBox(QCheckBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setMaximumWidth(MAX_WIDTH)

class PushButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setMaximumWidth(MAX_WIDTH)


if __name__ == '__main__':

    window = Widget()

    window.show()

    sys.exit(app.exec())
