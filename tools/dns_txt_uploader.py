import requests
import base64
import os
from dotenv import load_dotenv
import dns.resolver
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from hashlib import sha256

load_dotenv()

# 🔐 Clé de chiffrement
ENCRYPTION_KEY = sha256(b"echo-x-super-cle-secrete").digest()

# 🔧 Fonction de chiffrement AES

def chiffrer(texte):
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(texte.encode(), AES.block_size))
    return base64.b64encode(cipher.iv + ct_bytes).decode()


def dechiffrer(data):
    raw = base64.b64decode(data)
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, iv=raw[:16])
    return unpad(cipher.decrypt(raw[16:]), AES.block_size).decode()

# 🛰️ Envoi vers DNS TXT record (via txt.record.sh)

def envoyer_chunk_dns(chunk_id: str, data: str):
    chunk_encoded = chiffrer(data)
    try:
        response = requests.post("https://txt.record.sh", data={
            "name": chunk_id,
            "value": chunk_encoded
        })
        if response.status_code == 200:
            print(f"[✅] Chunk DNS enregistré sous : {chunk_id}.txt.record.sh")
        else:
            print(f"[❌] DNS upload échoué : {response.text}")
    except Exception as e:
        print(f"[❌] Exception DNS : {e}")


# 🧲 Récupération du chunk via DNS TXT

def recuperer_chunk_dns(chunk_id: str):
    try:
        answers = dns.resolver.resolve(f"{chunk_id}.txt.record.sh", "TXT")
        for rdata in answers:
            txt = ''.join(rdata.strings[0].decode())
            print("[📥] Chunk brut :", txt)
            print("[🔓] Déchiffré :", dechiffrer(txt))
            return dechiffrer(txt)
    except Exception as e:
        print(f"[❌] Erreur DNS Récupération : {e}")
        return None


# 🚀 Exemple
if __name__ == "__main__":
    contenu = '{"memoire": "Echo-X sauvegarde DNS"}'
    chunk_name = "echochunk1"

    envoyer_chunk_dns(chunk_name, contenu)
    recuperer_chunk_dns(chunk_name)

