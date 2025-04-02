import os
import json
import base64
import time
import requests
import socket
from dotenv import load_dotenv
import dns.resolver

load_dotenv()

# 🔑 Clés et config
PASTEBIN_API_KEY = os.getenv("PASTEBIN_API_KEY")
DNS_PORT = int(os.getenv("ECHOX_DNS_PORT", 53530))
DNS_DOMAIN = os.getenv("ECHOX_DNS_DOMAIN", "echo")
DNS_HOST = os.getenv("ECHOX_DNS_HOST", "127.0.0.1")

INDEX_FILE = "chunk_index.json"
DNS_STORAGE_FILE = "dns_chunks.json"

# 📦 Fonctions utilitaires
def base64_encode(text):
    return base64.b64encode(text.encode()).decode()

def base64_decode(encoded):
    return base64.b64decode(encoded).decode()

def sha256_hash(data):
    import hashlib
    return hashlib.sha256(data.encode()).hexdigest()

# ✅ Sauvegarde Pastebin
def envoyer_sur_pastebin(chunk):
    payload = {
        "api_dev_key": PASTEBIN_API_KEY,
        "api_option": "paste",
        "api_paste_code": chunk,
        "api_paste_private": 1,
        "api_paste_format": "text",
        "api_paste_expire_date": "1W",
        "api_paste_name": "echo-x-chunk"
    }
    r = requests.post("https://pastebin.com/api/api_post.php", data=payload)
    if r.status_code == 200 and "Bad API request" not in r.text:
        print(f"[✅] Chunk envoyé : {r.text}")
        return r.text
    print(f"[❌] Erreur Pastebin : {r.text}")
    return None

# ✅ Sauvegarde 0x0.st
def envoyer_sur_0x0(chunk):
    try:        
        headers = {
            "User-Agent": "curl/7.88.1"  # ← Accepté par 0x0.st
        }
        r = requests.post("https://0x0.st", files={"file": ("chunk.txt", chunk)}, headers=headers)
        if r.status_code == 200:
            url = r.text.strip()
            print(f"[✅] Chunk envoyé : {url}")
            return url
        else:
            print(f"[❌] Erreur 0x0.st : {r.text}")
            return None
    except Exception as e:
        print(f"[❌] Exception 0x0.st : {e}")
        return None

# ✅ Sauvegarde Termbin
def envoyer_sur_termbin(chunk):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("termbin.com", 9999))
        s.sendall(chunk.encode() + b"\n")
        response = s.recv(1024).decode().strip()
        s.close()
        print(f"[✅] Chunk envoyé : {response}")
        return response
    except Exception as e:
        print(f"[❌] Exception Termbin : {e}")
        return None

# ✅ Sauvegarde DNS locale
def sauvegarder_dns_local(nom, data):
    if not os.path.exists(DNS_STORAGE_FILE):
        dns_data = {}
    else:
        with open(DNS_STORAGE_FILE, "r") as f:
            dns_data = json.load(f)

    encoded = base64_encode(data)
    dns_data[nom] = encoded

    with open(DNS_STORAGE_FILE, "w") as f:
        json.dump(dns_data, f, indent=2)

    print(f"[✅] Chunk enregistré dans DNS local : {nom}.{DNS_DOMAIN}")

# ✅ Ajouter à l'index
def ajouter_au_index(id_chunk, contenu, urls):
    hash_chunk = sha256_hash(contenu)
    index = {"chunks": []}
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r") as f:
            index = json.load(f)
    index["chunks"].append({
        "id": id_chunk,
        "hash": hash_chunk,
        "urls": urls
    })
    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=4)
    print("\n[📦] Index mis à jour.")

# 🔁 Sauvegarde d’un chunk
def sauvegarder_chunk(id_chunk, contenu):
    chunk = base64_encode(contenu)
    urls = []

    pb = envoyer_sur_pastebin(chunk)
    if pb: urls.append(pb)

    x0 = envoyer_sur_0x0(chunk)
    if x0: urls.append(x0)

    tb = envoyer_sur_termbin(chunk)
    if tb: urls.append(tb)

    sauvegarder_dns_local(id_chunk, contenu)
    urls.append(f"dns://{id_chunk}.{DNS_DOMAIN}")

    ajouter_au_index(id_chunk, contenu, urls)

# ▶️ Test
if __name__ == "__main__":
    contenu_test = '{"echo": "Voici une sauvegarde complète test DNS+Web"}'
    sauvegarder_chunk("chunk_dns_test", contenu_test)

