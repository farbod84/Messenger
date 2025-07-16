import socket
from time import sleep
from encryption import Encryption
import pickle
from login import get

class User:
    def __init__(self):
        self.error = 0

        #make cutter to make intrupt bitween data
        self.cutter = b''
        for i in range(10):
            self.cutter += chr(i).encode()

        self.user_data = {}

        url = self.get_url()

        #get ip and port from url
        self.ip = url[0]
        self.port = int(url[1])

        self.username = self.user_data['username']
        self.encryption = Encryption()
        self.encryption.load_key(self.user_data['private_key'], self.user_data['password'])

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def wait_for_connect(self):
        connected = False
        while not connected:
            try:
                self.s.connect((self.ip, self.port))
                connected = True
            except:
                sleep(5)

    #connect to the server and authenticate
    def connect_server(self):
        try:
            self.wait_for_connect()
            self.s.send(self.username.encode())
            self.s.send(self.encryption.sign(self.s.recv(1024)))
            error = self.s.recv(1024).decode()
            if error != '0':
                self.error = 1000+int(error)
        except:
            self.error = 100

    #get server url from server.conf
    def get_url(self):
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
            try:
                with open('user_data.conf', 'rb') as file:
                    self.user_data = pickle.load(file)
            except:
                exit(0)
        return url


    #send data with encryption
    def send_data(self, destination_username, destination_public_key, data, is_file = False):
        #we don't send message for us, it's wierd!
        if destination_username == self.username: return

        #let encrypt it
        public_key = self.encryption.load_public_key(destination_public_key)
        data = self.encryption.encrypt(data, public_key, is_file)

        #ok so now we can send data
        destination_username = 'send:'+destination_username
        data += self.cutter
        self.s.send(destination_username.encode())
        sleep(0.1)

        self.s.send(data)
        sleep(max(0.1, len(data)/2e5))

        #lets also send the signture for they can trust us
        self.s.send(self.encryption.sign((destination_username[5:], data))+self.cutter)
        sleep(0.1)


    def change_info(self, new_user_data):
        #send change info order
        self.s.send(b'$change_info')
        sleep(0.1)

        #send new_user_data
        self.s.send(pickle.dumps(new_user_data))
        sleep(0.1)

        #lets make it more trust able
        self.s.send(self.encryption.sign(new_user_data))
        sleep(0.1)

        if not new_user_data['profile_image']:
            return

        #lets also send our profile
        with open(new_user_data['profile_image'], 'rb') as file:
            data = file.read()

        destination_username = 'send:$profile_image'
        data += self.cutter

        #now send the profile
        self.s.send(destination_username.encode())
        sleep(0.1)

        self.s.send(data)
        sleep(max(0.1, len(data)/2e5))

        #lets make it more trust able because just we can change our profile
        self.s.send(self.encryption.sign((destination_username[5:], data))+self.cutter)
        sleep(0.1)


    def check_user(self, username):
        username = 'valid:'+username
        self.s.send(username.encode())
        sleep(0.1)


    def recv_data(self):
        try:
            username = self.s.recv(1024).decode()
            if not username: return
        except: return
        if username[0] != '$' or username[:14] == '$profile_image':
            data = b''
            while data == b'' or data[-10:] != self.cutter:
                data += self.s.recv(1024)
            if username[:14] != '$profile_image':
                data = self.encryption.decrypt(data[:-10])
            else:
                with open(f'database/{username[15:]}.jpg', 'wb') as file:
                    file.write(data[:-10])
                return
        else:
            data = self.s.recv(1048576)
        if type(data) == type((0, 0)):
            return (username, data[0], True)
        return (username, data)