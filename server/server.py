import socket
import threading
import time
import pickle
from encryption import Encryption


class Send:
  def __init__(self, cutter, encryption, users, queue):
    self.cutter = cutter
    self.encryption = encryption
    self.users = users
    self.queue = queue


  def recv_data_and_sign(self, client_socket):
    data = b''
    while data == b'' or data[-10:] != self.cutter:
      data += client_socket.recv(1024)

    if self.cutter in data[:-10]:
      parts = data.split(self.cutter)
      data = parts[0]+self.cutter
      sign = parts[1]+self.cutter
    else:
      sign = b''
      while sign == b'' or sign[-10:] != self.cutter:
        sign += client_socket.recv(1024)

    return (data, sign)


  def send_message(self, destination, client_socket, username, user_data):
    user_destination = destination[5:]

    data, sign = self.recv_data_and_sign(client_socket)

    public_key = self.encryption.load_public_key(user_data['public_key'])
    if not self.encryption.verify((user_destination, data), sign[:-10], public_key):
      return False

    if self.update_profile(user_destination, username, data): return True

    self.sent(user_destination, username, data)

    return True


  def update_profile(self, user_destination, username, data):
    if user_destination == '$profile_image':
      with open(f'user_data/{username}.jpg', 'wb') as file:
        file.write(data[:-10])
      return True

    return False


  def sent(self, user_destination, username, data):
    try:
      self.users[user_destination].send(username.encode())
      time.sleep(0.1)

      self.users[user_destination].send(data)
      time.sleep(max(0.1, len(data)/2e5))
    except:
        if user_destination in self.queue:
          self.queue[user_destination].append((username, data))
        else:
          self.queue[user_destination] = [(username, data)]


class Files:
  def __init__(self):
    pass

  #make contact from user
  def make_contact_user(self, client_socket, username):
    user = self.open_userdata(client_socket, username)

    contact = {
      "messages": [],
      "username": user['username'],
      "bio": user['bio'],
      "profile_image": user['profile_image'],
      "phone": None,
      "public_key": user['public_key']
    }

    return contact


  def open_userdata(self, client_socket, username):
    try:
      with open(f'user_data/{username}', 'rb') as file:
        user_data = pickle.load(file)
    except:
      client_socket.send(b'404')
      return 
    return user_data


  def save_user_data(self, user_data):
    with open(f'user_data/{user_data['username']}', 'wb') as file:
      pickle.dump(user_data, file)


  #for checking the username is it allreasy exits
  def check_exits(self, user_data, client_socket):
    try:
      with open(f'user_data/{user_data['username']}', 'rb') as file:
        client_socket.send(b'1')
        return True
    except:
      return False


  def change_userdata_file(self, username, new_user_data):
    with open(f'user_data/{username}', 'wb') as file:
      pickle.dump(new_user_data, file)



class Server(Files):
  def __init__(self):
    self.cutter = b''
    for i in range(10):
      self.cutter += chr(i).encode()

    super().__init__()

    self.users = {}
    self.queue = {}
    self.encryption = Encryption()
    self.server_program()


  def authenticate(self, client_socket, username):
      user_data = self.open_userdata(client_socket, username)
      if not user_data: return

      #send time hash to sign
      public_key = self.encryption.load_public_key(user_data["public_key"])
      time_hash = self.encryption.hash(time.time())
      client_socket.send(time_hash)
      sign = client_socket.recv(1048576)

      #verfy the sign
      if not self.encryption.verify(time_hash, sign, public_key):
        client_socket.send(b'403')
        return False

      client_socket.send(b'0')
      time.sleep(0.1)

      return user_data


  def login(self, client_socket):
    username = client_socket.recv(1024).decode()

    user_data = self.open_userdata(client_socket, username)
    if not user_data: return

    #do some authenticate
    client_socket.send(user_data['private_key'])
    if self.authenticate(client_socket, username):
      client_socket.send(pickle.dumps(user_data))
    else:
      client_socket.send(b'403')


  def signup(self, client_socket):
    user_data = pickle.loads(client_socket.recv(1048576))

    #check username validity
    for e in '!@#$%^&*()-=+\'\\:;\".,/ \n\t':
      if e in user_data['username']:
        client_socket.send(b'2')
        return

    if self.check_exits(user_data, client_socket): return

    #done!
    self.save_user_data(user_data)
    client_socket.send(b'0')


  def send_the_queue(self, username, client_socket):
    if username not in self.queue: return

    for destination_username, send_data in self.queue[username]:
      client_socket.send(destination_username.encode())
      time.sleep(0.1)

      client_socket.send(send_data)
      time.sleep(max(0.1, len(send_data)/2e5))

    del self.queue[username]


  def handle_client(self, client_socket, address):
      username = client_socket.recv(1024).decode()

      if username == '$login':
        self.login(client_socket)
        return
      elif username == '$create_account':
        self.signup(client_socket)
        return

      #empty the queue
      self.send_the_queue(username, client_socket)

      user_data = self.authenticate(client_socket, username)
      if not user_data: return

      self.users[username] = client_socket
      print(f"Accepted connection from @{username} with address {address}")

      try:
        self.do_the_while(client_socket, username, user_data)
      except Exception as e:
        print(f"Error handling client {address}: {e}")
      finally:
        client_socket.close()
        print(f"Connection with {address} closed")


  #check user validity
  def validity(self, client_socket, destination):
    client_socket.send(b'$exist_user')
    time.sleep(0.1)
    try:
      contact = self.make_contact_user(client_socket, destination[6:])

      client_socket.send(pickle.dumps(contact))
      time.sleep(0.1)

      if contact['profile_image'] != None:
        client_socket.send((f'$profile_image {contact['username']}').encode())
        time.sleep(0.1)

        with open(f'user_data/{contact['username']}.jpg', 'rb') as file:
          data = file.read()

        client_socket.send(data+self.cutter)
        time.sleep(max(0.1, len(data)/2e5))
    except:
      client_socket.send(b'0')


  #change user info protocol
  def change_info(self, client_socket, username):
    new_user_data = pickle.loads(client_socket.recv(1048576))

    user_data = self.open_userdata(client_socket, username)
    if not user_data: return False

    public_key = self.encryption.load_public_key(user_data["public_key"])
    if not self.encryption.verify(new_user_data, client_socket.recv(1048576), public_key):
      return False

    if new_user_data['profile_image'] != None:
      new_user_data['profile_image'] = f'user_data/{username}.jpg'

    self.change_userdata_file(username, new_user_data)

    return True


  #for handeling the client we must have while
  def do_the_while(self, client_socket, username, user_data):
    send_object = Send(self.cutter, self.encryption, self.users, self.queue)

    while True:
      try:
        destination = client_socket.recv(1024).decode()
      except: continue

      if not destination or destination[:5] != 'send:':
        if destination[:6] == 'valid:':
          self.validity(client_socket, destination)
        elif destination == '$change_info':
          if not self.change_info(client_socket, username):
            continue
        continue

      if not send_object.send_message(destination, client_socket, username, user_data):
        break


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