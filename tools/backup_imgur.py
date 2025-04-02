import os
import base64
import requests
from stegano import lsb
from dotenv import load_dotenv
from PIL import Image

load_dotenv()
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")  # sinon None, on fera en anonyme

def chunk_to_image(chunk, output_path="chunk_hidden.png"):
    # Encode en base64
    encoded = base64.b64encode(chunk.encode()).decode()
    # Utilise une image vierge blanche 500x500
    image = Image.new("RGB", (500, 500), color=(255, 255, 255))
    image.save(output_path)
    # Cache le message
    lsb.hide(output_path, encoded).save(output_path)
    return output_path

def upload_to_imgur(image_path):
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    headers = {
        "Authorization": f"Client-ID {IMGUR_CLIENT_ID}" if IMGUR_CLIENT_ID else "Client-ID 5468bde2b1b30d1",  # clé publique par défaut
    }

    data = {
        "image": image_data,
        "type": "base64",
        "name": os.path.basename(image_path),
        "title": "Echo-X Backup Chunk"
    }

    r = requests.post("https://api.imgur.com/3/upload", headers=headers, data=data)
    if r.status_code == 200:
        url = r.json()["data"]["link"]
        print(f"[✅] Chunk envoyé sur Imgur : {url}")
        return url
    else:
        print(f"[❌] Erreur Imgur : {r.text}")
        return None

# Test
if __name__ == "__main__":
    test_data = '{"chunk": "backup LSB + imgur"}'
    image_path = chunk_to_image(test_data)
    upload_to_imgur(image_path)

