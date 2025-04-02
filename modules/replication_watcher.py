import os
import json
import time
from backup_manager import sauvegarder_chunk

INDEX_FILE = "chunk_index.json"
MEMORY_FILE = "memory.json"
DNS_STORAGE_FILE = "dns_chunks.json"

REPLICATION_INTERVAL = 900  # 15 minutes
replication_cache = {}

# 🔧 Vérifie si une URL est toujours accessible
def check_url_accessible(url):
    try:
        import requests
        r = requests.head(url, timeout=10)
        return r.status_code == 200
    except:
        return False

# 🔁 Réplication automatique
def surveiller_replicas():
    while True:
        if not os.path.exists(INDEX_FILE):
            time.sleep(30)
            continue

        try:
            with open(INDEX_FILE, "r") as f:
                content = f.read()
                if not content.strip():
                    print("[⚠️] Fichier index vide, on attend...")
                    time.sleep(30)
                    continue
                index = json.loads(content)
        except Exception as e:
            print(f"[❌] Erreur lecture index : {e}")
            time.sleep(30)
            continue

        # On ne garde qu’un seul chunk de mémoire (le plus récent)
        memoire_chunks = [c for c in index.get("chunks", []) if c["id"].startswith("memoire_")]
        autres_chunks = [c for c in index.get("chunks", []) if not c["id"].startswith("memoire_")]
        if memoire_chunks:
            memoire_chunks.sort(key=lambda x: x["id"], reverse=True)
            memoire_chunks = [memoire_chunks[0]]  # Garder uniquement le plus récent
        index["chunks"] = autres_chunks + memoire_chunks

        # Écrire l’index nettoyé
        try:
            with open(INDEX_FILE, "w") as f:
                json.dump(index, f, indent=4)
        except Exception as e:
            print(f"[❌] Erreur écriture index nettoyé : {e}")

        for chunk in index.get("chunks", []):
            chunk_id = chunk.get("id")
            urls = chunk.get("urls", [])
            disponibles = [u for u in urls if check_url_accessible(u)]
            print(f"[📦] {chunk_id} : {len(disponibles)}/3 disponibles")

            now = time.time()
            last_replication = replication_cache.get(chunk_id, 0)
            if len(disponibles) < 3 and now - last_replication > REPLICATION_INTERVAL:
                print(f"[⚠️] Réplication du chunk manquant : {chunk_id}")
                try:
                    if os.path.exists(DNS_STORAGE_FILE):
                        with open(DNS_STORAGE_FILE, "r") as f:
                            local_chunks = json.load(f)
                        contenu = local_chunks.get(chunk_id)
                        if contenu:
                            decoded = base64_decode(contenu)
                            sauvegarder_chunk(chunk_id, decoded)
                            replication_cache[chunk_id] = now
                        else:
                            print(f"[❌] Chunk {chunk_id} introuvable en local pour réplication.")
                    else:
                        print(f"[❌] DNS storage introuvable.")
                except Exception as e:
                    print(f"[❌] Erreur de réplication : {e}")
        time.sleep(60)

def base64_decode(encoded):
    import base64
    return base64.b64decode(encoded).decode()

if __name__ == "__main__":
    surveiller_replicas()

