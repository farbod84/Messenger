from PySide6.QtCore import QSize, Signal, QObject
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QAbstractItemView, QListWidgetItem, QMessageBox

from main import *
from client import User
from database import Database
import threading
import pickle
import uuid
import os, shutil

class ProfileTab(Widget):
    def __init__(self, user, client):
        super().__init__("My Profile")
        self.user = user
        self.client = client

        outer_layout = QVBoxLayout()
        top_bar = QHBoxLayout()
        top_bar.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.logout_btn = PushButton("Logout")
        self.logout_btn.setFixedSize(120, 40)
        self.logout_btn.clicked.connect(self.logout)
        top_bar.addWidget(self.logout_btn)
        outer_layout.addLayout(top_bar)

        layout = VBoxLayout()

        self.pic_label = QLabel()
        self.pic_label.setFixedSize(180, 180)
        self.pic_label.setStyleSheet("border: 3px solid gray; background: white; color: black;")
        self.pic_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_profile_picture(self.user['profile_image'])

        pic_layout = QHBoxLayout()
        pic_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pic_layout.addWidget(self.pic_label)

        self.change_pic_btn = PushButton("Change Profile Picture")
        self.change_pic_btn.clicked.connect(self.change_picture)

        self.username_lbl = Label(f"Username: {self.user['username']}")
        self.username_lbl.setStyleSheet("color: white;")
        self.phone_lbl = Label(f"Phone: {self.user['phone']}")
        self.phone_lbl.setStyleSheet("color: white;")

        self.bio_lbl = Label("Bio:")
        self.bio_lbl.setStyleSheet("color: white;")
        self.bio_edit = QTextEdit()
        self.bio_edit.setMaximumWidth(MAX_WIDTH)
        self.bio_edit.setText(self.user['bio'])
        self.bio_edit.setStyleSheet("font-size: 24px; padding: 10px; border-radius: 8px; border: 2px solid #ccc; background-color: white; color: black;")

        self.save_bio_btn = PushButton("Save Bio")
        self.save_bio_btn.clicked.connect(self.save_bio)

        layout.addLayout(pic_layout)
        layout.addWidget(self.change_pic_btn)
        layout.addSpacing(10)
        layout.addWidget(self.username_lbl)
        layout.addWidget(self.phone_lbl)
        layout.addSpacing(10)
        layout.addWidget(self.bio_lbl)
        layout.addWidget(self.bio_edit)
        layout.addWidget(self.save_bio_btn)

        outer_layout.addLayout(layout)
        self.setLayout(outer_layout)

    def set_profile_picture(self, path):
        if path:
            pixmap = QPixmap(path).scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.pic_label.setPixmap(pixmap)
        else:
            self.pic_label.setPixmap(QPixmap())
            self.pic_label.setText("No Image")

    def change_picture(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Profile Picture")
        if filename:
            self.user['profile_image'] = filename
            self.set_profile_picture(filename)
            with open('user_data.conf', 'wb') as file:
                pickle.dump(self.user, file)
            self.client.change_info(self.user)
            shutil.copy(filename, f'database/{self.user['username']}.jpg')

    def save_bio(self):
        self.user['bio'] = self.bio_edit.toPlainText()
        with open('user_data.conf', 'wb') as file:
            pickle.dump(self.user, file)
        self.client.change_info(self.user)

    def logout(self):
        os.remove('user_data.conf')
        os.remove('contacts.db')
        shutil.rmtree('database', ignore_errors=True)
        os.mkdir('database')
        os._exit(0)


class AddContactDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add New Contact")
        self.setFixedSize(400, 250)

        self.error_situation = 0

        layout = QVBoxLayout()
        form = QFormLayout()

        self.name_input = LineEdit()
        form.addRow("Name:", self.name_input)

        self.username_input = LineEdit()
        form.addRow("Username:", self.username_input)

        self.error_label = Label("Error")
        self.error_label.setStyleSheet("color: transparent;")

        layout.addLayout(form)
        layout.addWidget(self.error_label)

        btn = PushButton("Add")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

        self.setLayout(layout)

    def get_contact_info(self):
        return [self.name_input.text().strip(), self.username_input.text().strip()]

    def err(self):
        self.error_situation = 1 - self.error_situation
        if self.error_situation == 1:
            self.error_label.setStyleSheet("color: red;")
        else:
            self.error_label.setStyleSheet("color: transparent;")


class MessageWidget(QWidget):
    def __init__(self, content, sender='me', is_image=False):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        bubble = QLabel()
        bubble.setStyleSheet("""
            QLabel {
                border-radius: 12px;
                padding: 10px;
                font-size: 16px;
                background-color: %s;
                color: %s;
            }
        """ % (("white", "black") if sender == 'me' else ("#2e7d32", "white")))

        if is_image:
            pixmap = QPixmap(content)
            pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            bubble.setPixmap(pixmap)
            bubble.setFixedSize(pixmap.size())
        else:
            bubble.setText(content)
            bubble.setWordWrap(True)
            bubble.setMaximumWidth(300)

        if sender == 'me':
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            layout.addWidget(bubble)
            layout.addStretch()

        self.setLayout(layout)


class ContactHeaderWidget(QWidget):
    def __init__(self, contact):
        super().__init__()
        self.contact = contact
        self.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
            }
        """)
        self.setFixedHeight(120)

        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        self.pic = QLabel()
        self.pic.setFixedSize(80, 80)
        self.pic.setStyleSheet("background: #ccc; border: 2px solid white; color: black;")
        self.pic.setAlignment(Qt.AlignCenter)
        self.set_profile_picture(contact.get('profile_image'))

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.name_lbl = QLabel(f"{contact['name']}")
        self.name_lbl.setStyleSheet("font-weight: bold; font-size: 20px;")

        self.username_lbl = QLabel(f"@{contact.get('username', '')}")
        self.phone_lbl = QLabel(contact['phone'])
        self.bio_lbl = QLabel(contact.get('bio', ''))

        info_layout.addWidget(self.name_lbl)
        info_layout.addWidget(self.username_lbl)
        info_layout.addWidget(self.phone_lbl)
        info_layout.addWidget(self.bio_lbl)

        layout.addWidget(self.pic)
        layout.addLayout(info_layout)
        layout.addStretch()

        self.delete_btn = QPushButton("🗑 Delete Chat")
        self.delete_btn.setFixedSize(130, 40)
        self.delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #e53935;
                        color: white;
                        font-size: 16px;
                        border-radius: 6px;
                        padding: 6px 12px;
                    }
                    QPushButton:hover {
                        background-color: #b71c1c;
                    }
                """)
        layout.addWidget(self.delete_btn)

        self.setLayout(layout)

    def set_profile_picture(self, path):
        if path:
            pixmap = QPixmap(path).scaled(80, 80, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.pic.setPixmap(pixmap)
        else:
            self.pic.setText("No\nImage")

class ChatSignals(QObject):
    new_message = Signal(str, str, bool)


class Recv_client:
    def __init__(self, refresh_contact_list, contacts, database, current_contact, signals):
        self.signals = signals
        self.current_contact = current_contact
        self.refresh_contact_list = refresh_contact_list
        self.contacts = contacts
        self.database = database

        self.user = User()

        # for handeling the errors :
        if self.user.error == 404:
            print('private_key pem not found:(')
        elif self.user.error == 100:
            print('cannot make connection with server:(')
        elif self.user.error == 403:
            print('access deny! wrong password:(')
        else:
            print('connection successfully:)')

        thread = threading.Thread(target=self.recv_message)
        thread.start()


    #revice message and images
    def recv_message(self):
        while True:
            given = self.user.recv_data()
            if not given:
                self.refresh_contact_list()
                continue
            if len(given) == 2:
                username, data = given
                is_image = False
            else:
                username, data, is_image = given
            if username == '$exist_user':
                if data != b'0':
                    contact = pickle.loads(data)
                    if contact['profile_image']:
                        contact['profile_image'] = f'database/{contact['username']}.jpg'
                    found = False
                    for name in self.contacts:
                        if self.contacts[name]['username'] == contact['username']:
                            messages = self.contacts[name]['messages']
                            self.contacts[name] = contact
                            self.contacts[name]['messages'] = messages
                            self.contacts[name]['name'] = name
                            found = True
                            break
                    if not found and contact['username'] != self.user.username:
                        self.contacts[contact['username']] = contact
                        self.contacts[contact['username']]['messages'] = []
                    self.database.save_contact_list(self.contacts)
                    self.refresh_contact_list()
                continue
            if is_image:
                file_name = str(uuid.uuid4())
                with open(f'database/{file_name}.jpg', 'wb') as file:
                    file.write(data)
                data = f'database/{file_name}.jpg'
            found = False
            for name in self.contacts:
                if self.contacts[name]['username'] == username:
                    found = True
                    self.contacts[name]["messages"].append((data, 'other', is_image))
                    if name == self.current_contact:
                        self.signals.new_message.emit(data, 'other', is_image)
            if not found:
                if is_image:
                    self.contacts[username] = {"messages": [(data, 'other', is_image)], "username": username}
                else:
                    self.contacts[username] = {"messages": [(data, 'other')], "username": username}
                self.user.check_user(username)

class ChatTab(Widget, Recv_client):
    def __init__(self):
        Widget.__init__(self, "Chats")

        self.signals = ChatSignals()
        self.signals.new_message.connect(self.append_message)

        self.database = Database()

        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
        """)
        self.chat_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.chat_list.setSpacing(5)

        self.init_ui()

        Recv_client.__init__(self)

        for contact in self.contacts:
            self.user.check_user(self.contacts[contact]['username'])

    def init_ui(self):
        self.contacts = self.database.load_contacts()

        self.current_contact = list(self.contacts.keys())[0]

        layout = QHBoxLayout()
        left_panel = QVBoxLayout()

        self.add_contact_btn = PushButton("Add Contact")
        self.add_contact_btn.clicked.connect(self.show_add_contact_dialog)
        left_panel.addWidget(self.add_contact_btn)

        self.contact_list = QListWidget()
        self.contact_list.setMaximumWidth(300)
        self.contact_list.setStyleSheet("""
            QListWidget {
                font-size: 20px;
                padding: 10px;
                border: 2px solid #ccc;
                background-color: transparent;
                color: white;
            }
            QListWidget::item:selected {
                background-color: #0078D7;
                color: white;
            }
        """)
        left_panel.addWidget(self.contact_list)

        self.refresh_contact_list()

        right_panel = QVBoxLayout()

        self.header_widget = ContactHeaderWidget(self.contacts[self.current_contact])
        right_panel.addWidget(self.header_widget)
        self.contact_list.currentItemChanged.connect(self.change_chat)
        # self.chat_display.setMinimumHeight(600)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message...")
        self.input_field.setMinimumHeight(50)
        self.input_field.setStyleSheet("""
            QLineEdit {
                font-size: 20px;
                padding: 10px;
                border: 2px solid #ccc;
                border-radius: 8px;
                background-color: white;
                color: black;
            }
        """)

        self.send_btn = PushButton("Send")
        self.send_btn.setFixedSize(100, 50)
        self.send_btn.clicked.connect(self.send_message)

        self.image_btn = PushButton("📷")
        self.image_btn.setFixedSize(50, 50)
        self.image_btn.clicked.connect(self.send_image)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        input_layout.addWidget(self.image_btn)

        right_panel.addWidget(self.chat_list)
        right_panel.addLayout(input_layout)

        layout.addLayout(left_panel)
        layout.addLayout(right_panel)

        self.setLayout(layout)
        self.load_chat()


    def refresh_contact_list(self):
        self.contact_list.clear()
        delete_contacts = []
        for key, contact in self.contacts.items():
            if 'public_key' not in contact:
                delete_contacts.append(key)
                continue
            item = QListWidgetItem()

            item.setText(f"{contact['name']}")
            item.setFont(QFont("Arial", 18, QFont.Bold))
            item.setSizeHint(QSize(200, 80))

            if contact.get("profile_image"):
                pixmap = QPixmap(contact["profile_image"]).scaled(60, 60, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            else:
                pixmap = QPixmap(60, 60)
                pixmap.fill(Qt.gray)

            icon = QIcon(pixmap)
            item.setIcon(icon)

            self.contact_list.addItem(item)

        for key in delete_contacts:
            if len(self.contacts) > 1:
                del self.contacts[key]
            if key == self.current_contact:
                self.current_contact = list(self.contacts.keys())[0]

        self.contact_list.setIconSize(QSize(60, 60))
        self.contact_list.setCurrentRow(0)

    def show_add_contact_dialog(self):
        dialog = AddContactDialog()
        if dialog.exec():
            info = dialog.get_contact_info()
            self.contacts[info[0]] = {"name" : info[0], "messages" : [], "username" : info[1]}
            self.user.check_user(info[1])

    def change_chat(self, current):
        if current:
            self.current_contact = current.text()
            self.header_widget.setParent(None)
            self.header_widget = ContactHeaderWidget(self.contacts[self.current_contact])
            self.header_widget.delete_btn.clicked.connect(self.delete_current_chat)
            self.layout().itemAt(1).layout().insertWidget(0, self.header_widget)
            self.load_chat()

    def delete_current_chat(self):
        if self.contacts[self.current_contact]['username'] == self.user.username:
            return
        confirm = QMessageBox.question(self, "Delete Contact",
                                       f"Are you sure you want to delete contact {self.current_contact} and all related messages?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            del self.contacts[self.current_contact]  
            self.database.save_contact_list(self.contacts)

            self.refresh_contact_list()

            if self.contacts:
                self.current_contact = list(self.contacts.keys())[0]
                self.header_widget.setParent(None)
                self.header_widget = ContactHeaderWidget(self.contacts[self.current_contact])
                self.header_widget.delete_btn.clicked.connect(self.delete_current_chat)
                self.layout().itemAt(1).layout().insertWidget(0, self.header_widget)
                self.load_chat()
            else:
                self.chat_list.clear()
                self.header_widget.setParent(None)

    def load_chat(self):
        self.chat_list.clear()
        messages = self.contacts[self.current_contact]["messages"]
        for msg in messages:
            if type(msg[0]) == type(msg[1]) == type('str'):
                if len(msg) == 3:
                    self.append_message(msg[0], msg[1], msg[2])
                else:
                    self.append_message(msg[0], msg[1])
            else:
                del msg

    #send text message
    def send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return

        self.contacts[self.current_contact]["messages"].append((text, 'me'))
        self.append_message(text, 'me')

        public_key = self.contacts[self.current_contact]["public_key"]
        self.user.send_data(self.contacts[self.current_contact]["username"], public_key, text)

        self.input_field.clear()


    #send image data
    def send_image(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if filename:
            self.contacts[self.current_contact]["messages"].append((filename, 'me', True))
            self.append_message(filename, 'me', is_image=True)
            public_key = self.contacts[self.current_contact]["public_key"]
            self.user.send_data(self.contacts[self.current_contact]["username"], public_key, filename, True)

    #append message to the chat table
    def append_message(self, content: str, sender: str = 'me', is_image: bool = False):
        item_widget = MessageWidget(content, sender, is_image)
        list_item = QListWidgetItem()
        list_item.setSizeHint(item_widget.sizeHint())
        self.chat_list.addItem(list_item)
        self.chat_list.setItemWidget(list_item, item_widget)
        self.chat_list.scrollToBottom()
        self.database.save_contact_list(self.contacts)



class MessengerWindow(Widget):
    def __init__(self):
        super().__init__("Messenger")

        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tabs.tabBar().setStyleSheet("""
            QTabBar::tab {
                background-color: #0078D7;
                color: white;
                border: none;
                padding: 12px 60px;
                font-size: 24px;
                border-radius: 8px;
                min-width: 160px;
                margin: 2px;
            }
            QTabBar::tab:hover {
                background-color: #005a9e;
            }
            QTabBar::tab:selected {
                background-color: #005a9e;
            }
        """)

        chattab = ChatTab()
        self.tabs.addTab(chattab, "Chats")
        self.tabs.addTab(ProfileTab(chattab.user.user_data, chattab.user), "My Profile")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def closeEvent(self, event):
        event.accept()
        print('goodbye!')
        os._exit(0)


if __name__ == '__main__':
    window = MessengerWindow()
    window.show()
    sys.exit(app.exec())