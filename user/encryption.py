from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
import pickle

class Encryption:
    def __init__(self, private_key = None):
        self.__private_key = private_key
        self.cutter = b''
        for i in [23, 34, 13, 24, 95, 12, 84, 92, 4]:
            self.cutter += chr(i).encode()
        if private_key == None:
            self.create_new_key()
        else:
            self._public_key = self.__private_key.public_key()

    def create_new_key(self):
        self.__private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self._public_key = self.__private_key.public_key()

    def save_key(self, password):
        encrypted_pem = self.__private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.BestAvailableEncryption(password.encode()))
        return encrypted_pem

    def load_key(self, encrypted_pem, password):
        try:
            self.__private_key = serialization.load_pem_private_key(encrypted_pem, password=password.encode())
            self._public_key = self.__private_key.public_key()
            return True
        except:
            return False

    def to_bytes(self, var: object):
        bytes_data = pickle.dumps(var)
        return bytes_data

    def to_object(self, bytes_data: bytes):
        var = pickle.loads(bytes_data)
        return var

    def encrypt(self, data: object, public_key, is_file = False):
        if is_file:
            with open(data, 'rb') as file:
                data = file.read()
        elif type(data) != type(b'byte'):
            data = self.to_bytes(data)
        box_size = 100
        if len(data) > box_size:
            ciphertext = b''
            while len(data) > box_size:
                box_data = data[:box_size]
                ciphertext += public_key.encrypt(box_data, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
                ciphertext += self.cutter
                data = data[box_size:]
            ciphertext += public_key.encrypt(data, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
        else:
            ciphertext = public_key.encrypt(data, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
        if is_file:
            ciphertext += chr(15).encode()
        return ciphertext

    def decrypt(self, ciphertext: bytes):
        try:
            is_file = False
            if ciphertext[-1] == 15:
                ciphertext = ciphertext[:-1]
                is_file = True
            if self.cutter in ciphertext:
                ciphertext = ciphertext.split(self.cutter)
                data = b''
                for cipherbox in ciphertext:
                    data += self.__private_key.decrypt(cipherbox, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
            else:
                data = self.__private_key.decrypt(ciphertext, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
            if is_file:
                return (data, True)
            else:
                return self.to_object(data)
        except:
            return False

    def hash(self, var: object):
        data = self.to_bytes(var)
        digest = hashes.Hash(hashes.SHA256())
        digest.update(data)
        return digest.finalize()

    def sign(self, var: object):
        data = self.to_bytes(var)
        signature = self.__private_key.sign(data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
        return signature

    def verfy(self, var: object, signature, public_key):
        data = self.to_bytes(var)
        try:
            public_key.verify(signature, data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
            return True
        except:
            return False

    def __str__(self):
        pem_public = self._public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
        return pem_public.decode()

    def load_public_key(self, pem_public):
        public_key = serialization.load_pem_public_key(pem_public.encode())
        return public_key