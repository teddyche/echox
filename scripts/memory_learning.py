import json
import os

MEMORY_FILE = "memory.json"

# Charger ou initialiser la mémoire
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        memoire = json.load(f)
else:
    memoire = {
        "facts": {},
        "competences": {},
        "historique": []
    }

def sauvegarder():
    with open(MEMORY_FILE, "w") as f:
        json.dump(memoire, f, indent=4, ensure_ascii=False)

def enregistrer_fait(cle: str, valeur: str):
    memoire.setdefault("facts", {})[cle] = valeur
    sauvegarder()

def rappeler_fait(cle: str) -> str:
    return memoire.get("facts", {}).get(cle, "Je ne sais pas.")

# Exemple d'utilisation
if __name__ == "__main__":
    print("[Echo-X Mémoire Active]")
    while True:
        cmd = input("🔧 Commande (set/get/exit) > ").strip()
        if cmd == "exit":
            break
        elif cmd.startswith("set"):
            _, cle, *valeur = cmd.split()
            enregistrer_fait(cle, " ".join(valeur))
            print(f"✅ Fait enregistré : {cle} = {' '.join(valeur)}")
        elif cmd.startswith("get"):
            _, cle = cmd.split()
            print(f"📌 {cle} = {rappeler_fait(cle)}")
        else:
            print("❓ Commande inconnue. Utilise 'set cle valeur', 'get cle' ou 'exit'.")


