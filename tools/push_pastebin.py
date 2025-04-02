import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()  # ← Manquait ça !

PASTEBIN_API_KEY = os.getenv("PASTEBIN_API_KEY")
PASTEBIN_USER_KEY = None  # Facultatif

def sauvegarder_sur_pastebin(data: str, titre="echo-x-memory", expiration="1W"):
    chunk_encoded = base64.b64encode(data.encode()).decode()

    payload = {
        "api_dev_key": PASTEBIN_API_KEY,
        "api_option": "paste",
        "api_paste_name": titre,
        "api_paste_expire_date": expiration,
        "api_paste_private": 1,
        "api_paste_format": "text",
        "api_paste_code": chunk_encoded
    }

    if PASTEBIN_USER_KEY:
        payload["api_user_key"] = PASTEBIN_USER_KEY

    response = requests.post("https://pastebin.com/api/api_post.php", data=payload)
    
    if response.status_code == 200:
        print(f"[✅] Chunk envoyé : {response.text}")
        return response.text
    else:
        print(f"[❌] Erreur Pastebin : {response.text}")
        return None

# Test
if __name__ == "__main__":
    test_data = '{"echo": "je suis Echo-X, sauvegarde distribuée."}'
    sauvegarder_sur_pastebin(test_data)

