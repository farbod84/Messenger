from main import *
import pickle
import socket
from encryption import Encryption
from time import sleep

class Log_In(Widget):
    def __init__(self):
        super().__init__('Log In')

        main_layout = VBoxLayout()

        big_title = Label('Welcome Back!')
        big_title.setStyleSheet("font-size: 60px;")
        main_layout.addWidget(big_title)
        main_layout.addSpacing(30)

        username_input = LineEdit('Username')
        self.username_input = username_input
        main_layout.addWidget(self.username_input)

        password_input = LineEdit('Password', True)
        self.password_input = password_input
        main_layout.addWidget(self.password_input)

        show_password_checkbox = CheckBox('Show Password')
        show_password_checkbox.stateChanged.connect(self.password_input.set_password_visibility)
        main_layout.addWidget(show_password_checkbox)
        main_layout.addSpacing(20)

        login_button = PushButton('Login')
        self.login_button = login_button
        self.login_button.clicked.connect(self.login_button_clicked)
        main_layout.addWidget(self.login_button)
        main_layout.addSpacing(10)

        signup_button = PushButton("Don't have an account? Sign Up")
        self.signup_button = signup_button
        main_layout.addWidget(self.signup_button)

        self.setLayout(main_layout)

    def login_button_clicked(self):
        user_data = {
            'username' : self.username_input.text(),
            'password' : self.password_input.text(),
            'phone' : '',
            'bio' : '',
            'profile_image' : None
        }
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        url = ['', 0]
        try:
            with open('server.conf') as file:
                url = file.read().split(':')
            with open('user_data.conf', 'rb') as file:
                self.user_data = pickle.load(file)
        except:
            if url[0] == '':
                print('invalid server url')
                exit()
        s.connect((url[0], int(url[1])))
        s.sendall(b'$get_info')
        sleep(0.1)
        s.sendall(user_data['username'].encode())
        user_data['private_key'] = s.recv(1024).decode()
        if user_data['private_key'] == '404':
            #TODO invalid username
            return
        encryption = Encryption()
        if not encryption.load_key(user_data['private_key'], self.password_input.text()):
            #TODO invalid password
            return
        s.sendall(encryption.sign(s.recv(1024)))
        user_data = pickle.loads(s.recv(1024))
        with open('user_data.conf', 'wb') as file:
            pickle.dump(user_data, file)
        s.close()
        self.close()

class Sign_Up(Widget):
    def __init__(self):
        super().__init__('Sign Up')

        main_layout = VBoxLayout()

        big_title = Label('Hi!')
        big_title.setStyleSheet("font-size: 60px;")
        main_layout.addWidget(big_title)
        main_layout.addSpacing(30)

        username_input = LineEdit('Username')
        self.username_input = username_input
        main_layout.addWidget(self.username_input)

        phone_number_input = LineEdit('Phone Number')
        regex = QRegularExpression(r"\d{0,11}")
        validator = QRegularExpressionValidator(regex)
        phone_number_input.setValidator(validator)
        self.phone_number_input = phone_number_input
        main_layout.addWidget(self.phone_number_input)

        password_input = LineEdit('Password', True)
        self.password_input = password_input
        main_layout.addWidget(self.password_input)

        confirm_password_input = LineEdit('Confirm Password', True)
        self.confirm_password_input = confirm_password_input
        main_layout.addWidget(self.confirm_password_input)

        show_password_checkbox = CheckBox('Show Password')
        def show_password(state):
            self.password_input.set_password_visibility(state)
            self.confirm_password_input.set_password_visibility(state)
        show_password_checkbox.stateChanged.connect(show_password)
        main_layout.addWidget(show_password_checkbox)
        main_layout.addSpacing(20)

        signup_button = PushButton("Sign Up")
        self.signup_button = signup_button
        self.signup_button.clicked.connect(self.signup_button_clicked)
        main_layout.addWidget(self.signup_button)
        main_layout.addSpacing(10)

        login_button = PushButton('Have an account? Log In')
        self.login_button = login_button
        main_layout.addWidget(self.login_button)

        self.setLayout(main_layout)

    def signup_button_clicked(self):
        if self.password_input.text() != self.confirm_password_input.text():
            #TODO not same password
            return
        encryption = Encryption()
        password = self.password_input.text()
        user_data = {
            'username' : self.username_input.text(),
            'phone' : self.phone_number_input.text(),
            'private_key' : encryption.save_key(password),
            'public_key' : str(encryption),
            'bio' : '',
            'profile_image' : None
        }
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        url = ['', 0]
        try:
            with open('server.conf') as file:
                url = file.read().split(':')
            with open('user_data.conf', 'rb') as file:
                self.user_data = pickle.load(file)
        except:
            if url[0] == '':
                print('invalid server url')
                exit()
        s.connect((url[0], int(url[1])))
        s.sendall(b'$create_account')
        sleep(0.1)
        s.sendall(pickle.dumps(user_data))
        if s.recv(1024) == b'1':
            #TODO invalid username
            return
        user_data['password'] = password
        with open('user_data.conf', 'wb') as file:
            pickle.dump(user_data, file)
        s.close()
        self.close()

def get():
    window_log_in = Log_In()
    window_sign_up = Sign_Up()
    def sign_up_button_clicked():
        window_sign_up.show()
        window_log_in.close()
    def log_in_button_clicked():
        window_log_in.show()
        window_sign_up.close()
    window_log_in.signup_button.clicked.connect(sign_up_button_clicked)
    window_sign_up.login_button.clicked.connect(log_in_button_clicked)
    window_log_in.show()
    app.exec()

if __name__ == '__main__':
    get()