import requests
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from hashlib import sha256

# 🔐 Clé secrète partagée pour Echo-X
ENCRYPTION_KEY = sha256(b"echo-x-super-cle-secrete").digest()

def chiffrer_chunk(data: str) -> bytes:
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
    return base64.b64encode(cipher.iv + ct_bytes)

def sauvegarder_sur_0x0(data: str):
    chunk_encoded = base64.b64encode(data.encode()).decode()

    files = {
        'file': ('chunk.txt', chunk_encoded)
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.post("https://0x0.st", files=files, headers=headers)
        if response.status_code == 200 and response.text.startswith("https://"):
            url = response.text.strip()
            print(f"[✅] Chunk envoyé : {url}")
            return url
        else:
            print(f"[❌] Erreur 0x0.st : {response.text}")
            return None
    except Exception as e:
        print(f"[❌] Exception 0x0.st : {e}")
        return None

# 🎯 Test
if __name__ == "__main__":
    data = '{"echo": "sauvegarde distribuée, via 0x0.st"}'
    encrypted = chiffrer_chunk(data)
    envoyer_sur_0x0(encrypted.decode())

