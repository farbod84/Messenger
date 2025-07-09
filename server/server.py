import socket
import threading
import time
import pickle
from encryption import Encryption

class Server:
  def __init__(self):
    self.users = {}
    self.queue = {}
    self.encryption = Encryption()
    self.server_program()

  def autenticate(self, client_socket, username):
      user_data = None
      try:
        with open(f'user_data/{username}', 'rb') as file:
          user_data = pickle.load(file)
      except:
        client_socket.sendall(b'404')
        return
      public_key = self.encryption.load_public_key(user_data["public_key"])
      time_hash = self.encryption.hash(time.time())
      client_socket.sendall(time_hash)
      sign = client_socket.recv(1024)
      if not self.encryption.verfy(time_hash, sign, public_key):
        client_socket.sendall(b'403')
        return False
      client_socket.sendall(b'0')
      return user_data

  def handle_client(self, client_socket, address):
      username = client_socket.recv(1024).decode()
      if username == '$get_info':
        username = client_socket.recv(1024).decode()
        user_data = None
        try:
          with open(f'user_data/{username}', 'rb') as file:
            user_data = pickle.load(file)
        except:
          client_socket.sendall(b'404')
          return
        client_socket.sendall(user_data['private_key'].encode())
        if self.autenticate(client_socket, username):
          client_socket.sendall(pickle.dumps(user_data))
        else:
          client_socket.sendall(b'403')
        return
      elif username == '$create_account':
        user_data = pickle.loads(client_socket.recv(1048576))
        try:
          with open(f'user_data/{user_data['username']}', 'rb') as file:
            client_socket.sendall(b'1')
            return
        except:
          pass
        with open(f'user_data/{user_data['username']}', 'wb') as file:
          pickle.dump(user_data, file)
        client_socket.sendall(b'0')
        return
      user_data = self.autenticate(client_socket, username)
      if not user_data:
        return
      self.users[username] = client_socket
      print(f"Accepted connection from {username} with address {address}")
      if username in self.queue:
         for destination_username, send_data in self.queue[username]:
            client_socket.sendall(destination_username.encode())
            time.sleep(0.1)
            client_socket.sendall(send_data)
      try:
        while True:
          destination = client_socket.recv(1024).decode()
          if not destination or destination[:5] != 'send:':
            if destination[:6] == 'valid:':
              client_socket.sendall(b'$exist_user')
              time.sleep(0.1)
              try:
                with open(f'user_data/{destination[6:]}', 'rb') as file:
                  user = pickle.load(file)
                  contact = {
                    "messages": [],
                    "username": user['username'],
                    "bio": user['bio'],
                    "profile_image": user['profile_image'],
                    "phone": None,
                    "public_key": user['public_key']
                  }
                  client_socket.sendall(pickle.dumps(contact))
              except:
                client_socket.sendall(b'0')
            continue
          user_destination = destination[5:]
          data = b''
          while not data or data[-1] != b'\f':
            data += client_socket.recv(1024)
          if not self.encryption.verfy((user_destination, data), client_socket.recv(1048576), self.encryption.load_public_key(user_data['public_key'])):
            break
          try:
            self.users[user_destination].sendall(username.encode())
            time.sleep(0.1)
            self.users[user_destination].sendall(data.encode())
          except:
              if user_destination in self.queue:
                self.queue[user_destination].append((username, data))
              else:
                self.queue[user_destination] = [(username, data)]
      except Exception as e:
        print(f"Error handling client {address}: {e}")
      finally:
        client_socket.close()
        print(f"Connection with {address} closed")

  def server_program(self):
      host = '127.0.0.1'
      port = 5000

      self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.server_socket.bind((host, port))
      self.server_socket.listen()

      print(f"Server listening on {host}:{port}")
      try:
        while True:
            client_socket, address = self.server_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
            client_thread.start()
      except:
        self.server_socket.close()

if __name__ == '__main__':
    Server()