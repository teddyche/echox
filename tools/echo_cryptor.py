# tools/echo_cryptor.py

import base64
from Crypto.Cipher import AES, Blowfish
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

class EchoCrypto:
    def __init__(self):
        self.block_size_aes = AES.block_size  # 16
        self.block_size_blowfish = Blowfish.block_size  # 8

    def hex_key_to_bytes(self, hex_key: str) -> bytes:
        return bytes.fromhex(hex_key)

    def encrypt_aes(self, hex_key: str, plaintext: str) -> str:
        key = self.hex_key_to_bytes(hex_key)
        cipher = AES.new(key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(plaintext.encode(), self.block_size_aes))
        return base64.b64encode(cipher.iv + ct_bytes).decode()

    def decrypt_aes(self, hex_key: str, b64_data: str) -> str:
        key = self.hex_key_to_bytes(hex_key)
        raw = base64.b64decode(b64_data)
        iv = raw[:self.block_size_aes]
        ct = raw[self.block_size_aes:]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ct), self.block_size_aes).decode()

    def encrypt_blowfish(self, hex_key: str, plaintext: str) -> str:
        key = self.hex_key_to_bytes(hex_key)
        cipher = Blowfish.new(key, Blowfish.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(plaintext.encode(), self.block_size_blowfish))
        return base64.b64encode(cipher.iv + ct_bytes).decode()

    def decrypt_blowfish(self, hex_key: str, b64_data: str) -> str:
        key = self.hex_key_to_bytes(hex_key)
        raw = base64.b64decode(b64_data)
        iv = raw[:self.block_size_blowfish]
        ct = raw[self.block_size_blowfish:]
        cipher = Blowfish.new(key, Blowfish.MODE_CBC, iv)
        return unpad(cipher.decrypt(ct), self.block_size_blowfish).decode()

