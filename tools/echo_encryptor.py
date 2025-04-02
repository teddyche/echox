#!/usr/bin/env python3
# tools/echo_encryptor.py

import sys
from echo_crypto import EchoCrypto

if len(sys.argv) != 4:
    print("Usage : python echo_encryptor.py <aes|blowfish|rc4> <hex_key> <message>")
    sys.exit(1)

method = sys.argv[1].lower()
key_hex = sys.argv[2]
message = sys.argv[3]

crypto = EchoCrypto()

try:
    if method == "aes":
        b64 = crypto.encrypt_aes(key_hex, message)
    elif method == "blowfish":
        b64 = crypto.encrypt_blowfish(key_hex, message)
    elif method == "rc4":
        b64 = crypto.encrypt_rc4(key_hex, message)
    else:
        print("[❌] Méthode de chiffrement non supportée.")
        print("Usage : python echo_encryptor.py <aes|blowfish|rc4> <hex_key> <message>")
        sys.exit(1)

    print(f"[🔒] Base64 chiffré : {b64}")

except Exception as e:
    print(f"[❌] Erreur : {e}")

