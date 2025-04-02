import os
import sys
import json
import base64
import hashlib
import tarfile
import requests
import time
from dotenv import load_dotenv
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from modules.backup_manager import sauvegarder_chunk

# === Init chemins robustes ===
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODULES_DIR = os.path.join(ROOT_DIR, 'modules')

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if MODULES_DIR not in sys.path:
    sys.path.insert(0, MODULES_DIR)

# === Configs ===
load_dotenv()
CHUNK_SIZE = 256 * 1024  # 256 Ko
ENCRYPTION_KEY = os.getenv("ECHOX_AES_KEY", "default_key_32_bytes__").encode()[:32]

REGEN_DIR = "regeneration"
ARCHIVE_NAME = f"{REGEN_DIR}/regen_package.tar.gz"
CHUNK_PREFIX = "regen_"
CHUNK_STORAGE = {}

FILES_TO_INCLUDE = [
    "core.py", "chunk_index.json", "requirements.txt", ".env",
    "tools/", "scripts/", "modules/", "templates/"
]

os.makedirs(REGEN_DIR, exist_ok=True)

# === Utilitaires ===
def check_url_accessible(url):
    try:
        if url.startswith("dns://"):
            return True  # DNS local = toujours dispo
        r = requests.get(url, timeout=10)
        return r.status_code == 200
    except:
        return False

def load_chunk_from_dns(chunk_id):
    path = "dns_chunks.json"
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            dns_data = json.load(f)
        encoded = dns_data.get(chunk_id)
        if encoded:
            return encoded
    except:
        return None
    return None

def verifier_chunks_regen():
    if not os.path.exists("chunk_index.json"):
        print("[❌] Aucun index de chunk trouvé.")
        return

    with open("chunk_index.json", "r") as f:
        index = json.load(f)

    regen_chunks = [c for c in index.get("chunks", []) if c["id"].startswith("regen_")]
    for chunk in regen_chunks:
        chunk_id = chunk["id"]
        urls = chunk["urls"]
        accessibles = [u for u in urls if check_url_accessible(u)]
        print(f"[🔍] {chunk_id} : {len(accessibles)}/{len(urls)} disponibles")
        if len(accessibles) < 3:
            print(f"[⚠️] Tentative de réplication de {chunk_id}")
            contenu = CHUNK_STORAGE.get(chunk_id)
            if not contenu:
                contenu = load_chunk_from_dns(chunk_id)
                if contenu:
                    CHUNK_STORAGE[chunk_id] = contenu
            if contenu:
                sauvegarder_chunk(chunk_id, contenu)
            else:
                print(f"[❌] Chunk {chunk_id} introuvable pour réplication.")

def create_tar_archive(output_path):
    with tarfile.open(output_path, "w:gz") as tar:
        for path in FILES_TO_INCLUDE:
            if os.path.exists(path):
                tar.add(path)
    print(f"[📦] Archive créée : {output_path}")

def pad(data):
    pad_len = AES.block_size - (len(data) % AES.block_size)
    return data + bytes([pad_len]) * pad_len

def encrypt_file(in_path):
    with open(in_path, "rb") as f:
        data = f.read()
    iv = get_random_bytes(16)
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(data))
    return iv + encrypted

def split_chunks(binary_data):
    chunks = [binary_data[i:i + CHUNK_SIZE] for i in range(0, len(binary_data), CHUNK_SIZE)]
    print(f"[✂️] Archive découpée en {len(chunks)} chunks.")
    return chunks

def encode_base64(chunks):
    return [base64.b64encode(chunk).decode() for chunk in chunks]

def creer_regeneration_archive():
    print("[⚙️] Démarrage de la création de l'archive de régénération...")
    create_tar_archive(ARCHIVE_NAME)
    encrypted_data = encrypt_file(ARCHIVE_NAME)
    chunks = split_chunks(encrypted_data)
    chunks_b64 = encode_base64(chunks)

    for i, chunk_b64 in enumerate(chunks_b64):
        chunk_id = f"{CHUNK_PREFIX}{i:02d}"
        CHUNK_STORAGE[chunk_id] = chunk_b64
        sauvegarder_chunk(chunk_id, chunk_b64)
        time.sleep(1)  # anti-spam

    print("[✅] Archive de régénération sauvegardée.")

# === Exécution directe
if __name__ == "__main__":
    creer_regeneration_archive()

