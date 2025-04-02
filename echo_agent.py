# echo_agent.py

import os
import json
import time
import requests

CURRENT_PORT_FILE = "logs/current_port.txt"

def get_echox_url():
    """
    Lit le fichier contenant le port dynamique de Echo-X et retourne l'URL complète.
    """
    if not os.path.exists(CURRENT_PORT_FILE):
        print("[❌] Fichier de port introuvable. Echo-X est-il lancé ?")
        return None
    try:
        with open(CURRENT_PORT_FILE, "r") as f:
            url = f.read().strip()
            if url:
                print(f"[🔌] Connexion à Echo-X sur {url}")
                return url
    except Exception as e:
        print(f"[❌] Erreur lecture port : {e}")
    return None

def interroger_echox(message, base_url):
    """
    Envoie un message à Echo-X et retourne la réponse.
    """
    try:
        r = requests.post(f"{base_url}/talk", json={"message": message}, timeout=10)
        data = r.json()
        return data.get("reponse", "[❌] Aucune réponse.")
    except Exception as e:
        return f"[❌] Erreur communication Echo-X : {e}"

def boucle_interactive():
    """
    Boucle REPL interactive avec Echo-X.
    """
    url = get_echox_url()
    if not url:
        return

    print("🤖 Echo-Agent connecté. Tape 'exit' pour quitter.\n")
    while True:
        try:
            msg = input("🧍 Toi > ").strip()
            if msg.lower() in ["exit", "quit"]:
                print("👋 À bientôt.")
                break
            if not msg:
                continue
            réponse = interroger_echox(msg, url)
            print(f"🤖 Echo > {réponse}\n")
        except KeyboardInterrupt:
            print("\n👋 Fin de session.")
            break

if __name__ == "__main__":
    boucle_interactive()

