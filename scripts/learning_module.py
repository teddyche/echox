import os
import json
from modules.distilgpt2_engine import DistilGPT2Engine

MEMORY_FILE = "memory.json"
llm = DistilGPT2Engine()

# Charger la mémoire existante
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        memoire = json.load(f)
else:
    memoire = {
        "competences": {},
        "historique": []
    }

def sauvegarder_memoire():
    with open(MEMORY_FILE, "w") as f:
        json.dump(memoire, f, indent=4, ensure_ascii=False)

def learn_and_remember(question: str) -> str:
    # Si déjà connue
    if question in memoire.get("competences", {}):
        return memoire["competences"][question]

    # Générer une réponse avec le LLM
    reponse = llm.generate(question)

    # Enregistrer en compétence
    if len(reponse.strip()) > 10:
        memoire["competences"][question] = reponse.strip()
        memoire["historique"].append({"q": question, "r": reponse.strip()})
        sauvegarder_memoire()

    return reponse

# Test manuel
if __name__ == "__main__":
    while True:
        q = input("🧠 Pose une question à Echo-X : ")
        if q.lower() in ["exit", "quit"]:
            break
        r = learn_and_remember(q)
        print(f"🤖 {r}\n")

