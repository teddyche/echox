import socket
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from hashlib import sha256

# Clé de chiffrement (même que pour le reste)
ENCRYPTION_KEY = sha256(b"echo-x-super-cle-secrete").digest()

def chiffrer(texte):
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(texte.encode(), AES.block_size))
    return base64.b64encode(cipher.iv + ct_bytes).decode()

def sauvegarder_sur_termbin(data: str):
    chunk = chiffrer(data)

    try:
        with socket.create_connection(("termbin.com", 9999), timeout=10) as s:
            s.sendall(chunk.encode() + b"\n")
            response = s.recv(1024).decode().strip()
            print(f"[✅] Chunk envoyé : {response}")
            return response
    except Exception as e:
        print(f"[❌] Erreur Termbin : {e}")
        return None

# Test
if __name__ == "__main__":
    test_data = '{"echo": "je suis Echo-X, sauvegarde distribuée via Termbin."}'
    sauvegarder_termbin(test_data)

