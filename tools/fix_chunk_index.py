import json
import os

FILE = "chunk_index.json"
BACKUP = "chunk_index_corrupt_backup.json"

print("🔧 Réparation structurelle de chunk_index.json...")

try:
    with open(FILE, "r") as f:
        raw = f.read()
except FileNotFoundError:
    print("❌ Fichier chunk_index.json introuvable.")
    exit(1)

# Sauvegarde
with open(BACKUP, "w") as f:
    f.write(raw)
print(f"📦 Backup sauvegardé -> {BACKUP}")

# Extraction ligne par ligne
lines = raw.splitlines()
valid_chunks = []
current = []
in_chunk = False

for line in lines:
    if '"id":' in line:
        in_chunk = True
        current = [line]
    elif in_chunk:
        current.append(line)
        if "}" in line:
            # Tentative de chargement
            try:
                chunk_json = json.loads("{\n" + "\n".join(current) + "\n}")
                valid_chunks.append(chunk_json)
                in_chunk = False
            except:
                in_chunk = False  # abandonner ce bloc

# Reconstruction
final_data = {"chunks": valid_chunks}
try:
    with open(FILE, "w") as f:
        json.dump(final_data, f, indent=2)
    print(f"✅ {len(valid_chunks)} chunks valides récupérés.")
except Exception as e:
    print(f"❌ Erreur finale : {e}")

