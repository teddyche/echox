import os
import json
import base64
import requests

INDEX_FILE = "chunk_index.json"
DNS_STORAGE_FILE = "dns_chunks.json"

# 🔁 Récupère le chunk mémoire actif
def get_latest_memory_chunk():
    if not os.path.exists(INDEX_FILE):
        print("[❌] Fichier index introuvable")
        return None

    with open(INDEX_FILE, "r") as f:
        index = json.load(f)

    chunks = [c for c in index.get("chunks", []) if c["id"].startswith("memoire_")]
    if not chunks:
        print("[❌] Aucun chunk mémoire trouvé dans l’index")
        return None

    chunks.sort(key=lambda x: x["id"], reverse=True)
    return chunks[0]

# 📦 Tente de récupérer depuis DNS local d'abord
def read_chunk_from_dns(chunk_id):
    if not os.path.exists(DNS_STORAGE_FILE):
        return None
    with open(DNS_STORAGE_FILE, "r") as f:
        data = json.load(f)
    encoded = data.get(chunk_id)
    if encoded:
        try:
            return base64.b64decode(encoded).decode()
        except:
            return None
    return None

# 🌍 Récupère depuis URL HTTP si pas dispo localement
def read_chunk_from_web(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return base64.b64decode(r.text.strip()).decode()
    except:
        return None
    return None

# 🧠 Fonction principale
def restaurer_memoire():
    chunk = get_latest_memory_chunk()
    if not chunk:
        return

    chunk_id = chunk["id"]
    print(f"[🔍] Restauration de la mémoire depuis : {chunk_id}")

    contenu = read_chunk_from_dns(chunk_id)
    if contenu:
        print("[✅] Mémoire restaurée depuis DNS local:\n")
        print(contenu)
        return

    for url in chunk["urls"]:
        if url.startswith("http"):
            contenu = read_chunk_from_web(url)
            if contenu:
                print(f"[✅] Mémoire restaurée depuis {url} :\n")
                print(contenu)
                return

    print("[❌] Impossible de restaurer la mémoire.")

if __name__ == "__main__":
    restaurer_memoire()

