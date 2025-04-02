import time
import json
import os
import requests
from push_pastebin import sauvegarder_sur_pastebin
from upload_0x0 import sauvegarder_sur_0x0
from termbin import sauvegarder_sur_termbin

INDEX_FILE = "chunk_index.json"
MIN_REPLICAS = 3
CHECK_INTERVAL = 60  # seconds

platforms = {
    "pastebin": sauvegarder_sur_pastebin,
    "0x0": sauvegarder_sur_0x0,
    "termbin": sauvegarder_sur_termbin
}

def charger_index():
    if not os.path.exists(INDEX_FILE):
        return {"chunks": []}
    with open(INDEX_FILE, "r") as f:
        return json.load(f)

def sauvegarder_index(index):
    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=4)

def verifier_url(url):
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except:
        return False

def repliquer_chunk(chunk):
    actif_sources = {
        name: url for name, url in chunk["sources"].items() if verifier_url(url)
    }
    manquantes = [p for p in platforms if p not in actif_sources]

    if len(actif_sources) >= MIN_REPLICAS:
        return False  # Pas besoin de répliquer

    print(f"[🔁] Chunk {chunk['id']} a besoin de répliques: {manquantes}")
    for p in manquantes:
        try:
            url = platforms[p](chunk["content"])
            if url:
                chunk["sources"][p] = url
                if len(chunk["sources"]) >= MIN_REPLICAS:
                    break
        except Exception as e:
            print(f"[⚠️] Erreur lors du push sur {p} : {e}")
    return True

def boucle_index():
    while True:
        print("\n[📡] Vérification des chunks en cours...")
        index = charger_index()
        modif = False
        for chunk in index["chunks"]:
            if repliquer_chunk(chunk):
                modif = True
        if modif:
            sauvegarder_index(index)
        print("[✅] Vérification terminée. Nouvelle itération dans 60s.")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    boucle_index()

