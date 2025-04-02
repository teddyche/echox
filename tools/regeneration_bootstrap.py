import os
import base64
import tarfile
import json
import time
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from dotenv import load_dotenv

load_dotenv(dotenv_path="./.env")
AES_KEY = os.getenv("ECHOX_AES_KEY")
if not AES_KEY or len(AES_KEY) != 32:
    raise ValueError("❌ Clé AES invalide ou manquante (32 caractères requis).")

AES_KEY = AES_KEY.encode()

INDEX_FILE = "data/chunk_index.json"
REGEN_PREFIX = "regen_"
REGEN_OUTPUT = "/tmp/echo-x_regenerated.tar.gz"
EXTRACTION_DIR = "echo-x_restored"

def get_chunks_from_index():
    if not os.path.exists(INDEX_FILE):
        print("[❌] Index introuvable.")
        return []

    with open(INDEX_FILE, "r") as f:
        index = json.load(f)

    regen_chunks = [c for c in index.get("chunks", []) if c["id"].startswith(REGEN_PREFIX)]
    regen_chunks.sort(key=lambda c: c["id"])  # Assure l'ordre
    return regen_chunks

def download_chunk(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return base64.b64decode(r.text.strip())
    except Exception as e:
        print(f"[❌] Erreur de téléchargement : {e}")
    return None

def decrypt_data(data):
    iv = data[:16]
    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(data[16:])
    return unpad(decrypted, AES.block_size)

def reassembler_chunks(chunks):
    full_data = b""
    for chunk in chunks:
        contenu = None
        for url in chunk["urls"]:
            if url.startswith("http"):
                contenu = download_chunk(url)
                if contenu:
                    break
        if contenu:
            try:
                decrypted = decrypt_data(contenu)
                full_data += decrypted
            except Exception as e:
                print(f"[❌] Erreur déchiffrement chunk {chunk['id']}: {e}")
                return None
        else:
            print(f"[❌] Chunk {chunk['id']} indisponible.")
            return None
    return full_data

def extraire_archive(path):
    if not tarfile.is_tarfile(path):
        print("[❌] Archive invalide.")
        return False
    with tarfile.open(path, "r:gz") as tar:
        tar.extractall(EXTRACTION_DIR)
    return True

def restaurer_et_lancer():
    chunks = get_chunks_from_index()
    if not chunks:
        print("[❌] Aucun chunk de régénération trouvé.")
        return

    print(f"[📦] {len(chunks)} chunks trouvés. Début de la reconstruction...")
    archive_data = reassembler_chunks(chunks)

    if not archive_data:
        print("[❌] Reconstruction échouée.")
        return

    with open(REGEN_OUTPUT, "wb") as f:
        f.write(archive_data)

    print(f"[✅] Archive reconstituée : {REGEN_OUTPUT}")
    print("[📂] Extraction...")
    if extraire_archive(REGEN_OUTPUT):
        print(f"[✅] Extraction terminée dans ./{EXTRACTION_DIR}")
        print("🚀 Lancement de Echo-X...")
        os.system(f"cd {EXTRACTION_DIR} && source venv/bin/activate && python core.py")
    else:
        print("[❌] Extraction échouée.")

if __name__ == "__main__":
    restaurer_et_lancer()

