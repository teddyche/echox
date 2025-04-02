# tools/echo_crypto.py

from Crypto.Cipher import AES, Blowfish, ARC4
from Crypto.Util.Padding import pad, unpad
import base64

class EchoCrypto:
    @staticmethod
    def encrypt_aes(key_hex, plaintext):
        key = bytes.fromhex(key_hex)
        cipher = AES.new(key, AES.MODE_ECB)
        ciphertext = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
        return base64.b64encode(ciphertext).decode()

    @staticmethod
    def decrypt_aes(key_hex, b64_data):
        key = bytes.fromhex(key_hex)
        cipher = AES.new(key, AES.MODE_ECB)
        ciphertext = base64.b64decode(b64_data)
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return plaintext.decode()

    @staticmethod
    def encrypt_blowfish(key_hex, plaintext):
        key = bytes.fromhex(key_hex)
        cipher = Blowfish.new(key, Blowfish.MODE_ECB)
        ciphertext = cipher.encrypt(pad(plaintext.encode(), Blowfish.block_size))
        return base64.b64encode(ciphertext).decode()

    @staticmethod
    def decrypt_blowfish(key_hex, b64_data):
        key = bytes.fromhex(key_hex)
        cipher = Blowfish.new(key, Blowfish.MODE_ECB)
        ciphertext = base64.b64decode(b64_data)
        plaintext = unpad(cipher.decrypt(ciphertext), Blowfish.block_size)
        return plaintext.decode()

    def encrypt_rc4(self, key_hex, message):
        key = bytes.fromhex(key_hex)
        cipher = ARC4.new(key)
        encrypted = cipher.encrypt(message.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt_rc4(self, key_hex, b64_data):
        key = bytes.fromhex(key_hex)
        data = base64.b64decode(b64_data)
        cipher = ARC4.new(key)
        decrypted = cipher.decrypt(data)
        return decrypted.decode()
