import socket
from time import sleep
from encryption import Encryption
import pickle
from login import get

class User:
    def __init__(self):
        self.error = 0
        self.user_data = {}
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
            get()
            with open('user_data.conf', 'rb') as file:
                self.user_data = pickle.load(file)
        self.ip = url[0]
        self.port = int(url[1])
        self.username = self.user_data['username']
        self.encryption = Encryption()
        self.encryption.load_key(self.user_data['private_key'], self.user_data['password'])
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.s.connect((self.ip, self.port))
            self.s.sendall(self.username.encode())
            self.s.sendall(self.encryption.sign(self.s.recv(1024)))
            error = self.s.recv(1024).decode()
            if error != '0':
                self.error = 1000+int(error)
        except:
            self.error = 100

    def send_data(self, destination_username, destination_public_key, data):
        data = self.encryption.encrypt(data, self.encryption.load_public_key(destination_public_key))
        destination_username = 'send:'+destination_username
        data += b'\f'
        self.s.sendall(destination_username.encode())
        sleep(0.1)
        self.s.sendall(data)
        sleep(0.1)
        self.s.sendall(self.encryption.sign((destination_username[5:], data)))

    def check_user(self, username):
        username = 'valid:'+username
        self.s.sendall(username.encode())

    def recv_data(self):
        username = self.s.recv(1024).decode()
        if username[0] != '$':
            data = b''
            while not data or data[-1] != b'\f':
                data += self.s.recv(1024)
            data = self.encryption.decrypt(data[:-1])
        else:
            data = self.s.recv(1048576)
        return (username, data)