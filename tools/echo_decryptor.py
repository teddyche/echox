# tools/echo_decryptor.py

import sys
from echo_crypto import EchoCrypto

def usage():
    print("Usage : python echo_decryptor.py <aes|blowfish> <hex_key> <base64_chiffre>")
    sys.exit(1)

if len(sys.argv) != 4:
    usage()

method = sys.argv[1].lower()
key_hex = sys.argv[2]
b64_data = sys.argv[3]

crypto = EchoCrypto()

try:
    if method == "aes":
        message = crypto.decrypt_aes(key_hex, b64_data)
    elif method == "blowfish":
        message = crypto.decrypt_blowfish(key_hex, b64_data)
    elif method == "rc4":
        message = crypto.decrypt_rc4(key_hex, b64_data)
    else:
        print("[❌] Méthode de déchiffrement non supportée.")
        usage()
    print(f"[🔓] Message déchiffré : {message}")
except Exception as e:
    print(f"[❌] Erreur : {e}")

