# tools/dns_resolver.py

import socket
import dns.resolver
import requests
import urllib.parse
from dns.exception import DNSException
from dns.resolver import Resolver

def resolve_domain(domain):
    print(f"[🧠 DNS] 🧪 Résolution de {domain}...")

    # Méthode 1 : Résolution classique
    try:
        ip = socket.gethostbyname(domain)
        print(f"[🧠 DNS] ✅ Résolu via socket.gethostbyname : {ip}")
        return [ip]
    except Exception as e:
        print(f"[🧠 DNS] ❌ Résolution classique échouée : {e}")

    # Méthode 2 : Résolution via DNS "brute" (sans resolv.conf)
    for nameserver in ["8.8.8.8", "1.1.1.1"]:
        try:
            resolver = Resolver(configure=False)
            resolver.nameservers = [nameserver]
            answers = resolver.resolve(domain)
            ips = [answer.address for answer in answers]
            print(f"[🧠 DNS] ✅ Résolu via fallback DNS {nameserver} : {ips}")
            return ips
        except DNSException as e:
            print(f"[🧠 DNS] ⚠️ Fallback DNS {nameserver} échoué : {e}")

    # Méthode 3 : DNS-over-HTTPS (DoH)
    try:
        url = f"https://dns.google/resolve?name={urllib.parse.quote(domain)}&type=A"
        headers = {"accept": "application/dns-json"}
        r = requests.get(url, timeout=5, headers=headers)
        r.raise_for_status()
        data = r.json()
        ips = [a["data"] for a in data.get("Answer", []) if a.get("type") == 1]
        if ips:
            print(f"[🧠 DNS] ✅ Résolu via DoH (dns.google) : {ips}")
            return ips
        else:
            print("[🧠 DNS] ❌ DoH réponse vide")
    except Exception as e:
        print(f"[🧠 DNS] ❌ Résolution DoH échouée : {e}")

    return []

# ▶️ Test manuel
if __name__ == "__main__":
    print(resolve_domain("openai.com"))

