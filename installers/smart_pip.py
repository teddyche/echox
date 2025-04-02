#!/usr/bin/env python3
# smart_pip_install.py

import subprocess
import sys
import os
import importlib.util
import socket
import argparse

# Charger dns_resolver_best dynamiquement
spec = importlib.util.spec_from_file_location("dns_resolver", "tools/dns_resolver_best.py")
dns_resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dns_resolver)

def run_command(command, check=True):
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if check and result.returncode != 0:
        print(f"[ERROR] Command failed: {command}")
        print(f"Output: {result.stdout}")
        print(f"Error: {result.stderr}")
    return result

def check_pip_connectivity(package):
    print(f"[INFO] Test de connexion à PyPI pour {package}...")
    result = run_command(f"pip install {package} --dry-run", check=False)
    return result.returncode == 0

def resolve_pypi_ip():
    print("[INFO] Résolution alternative de pypi.org via dns_resolver_best...")
    try:
        ips = dns_resolver.resolve_domain("pypi.org", test_all=True, quick=True)
        if ips:
            print(f"[INFO] IPs trouvées pour pypi.org : {ips}")
            return ips[0]
        else:
            raise Exception("Pas d’IP trouvée.")
    except Exception as e:
        raise Exception(f"Échec de résolution via dns_resolver_best: {e}")

def smart_pip_install(package, force_fallback=False):
    # Option pour forcer l'échec DNS standard
    if force_fallback:
        socket.gethostbyname = lambda x: (_ for _ in ()).throw(OSError("Forced DNS failure"))

    if not force_fallback and check_pip_connectivity(package):
        print(f"[INFO] Connexion à PyPI OK, installation de {package}...")
        result = run_command(f"pip install {package}")
        if result.returncode == 0:
            print(f"[SUCCESS] {package} installé avec succès.")
            return True
        else:
            print("[WARNING] pip install standard a échoué.")

    print("[INFO] Tentative de fallback avec IP directe...")
    try:
        pypi_ip = resolve_pypi_ip()
    except Exception as e:
        print(f"[ERROR] Fallback DNS impossible : {e}")
        return False

    pypi_url = f"https://{pypi_ip}/"
    result = run_command(
        f"pip install {package} --index-url {pypi_url} --trusted-host pypi.org",
        check=False
    )

    if result.returncode == 0:
        print(f"[SUCCESS] {package} installé avec succès via IP {pypi_ip}.")
        return True
    else:
        print(f"[ERROR] Échec de l'installation même avec fallback IP.")
        print(f"Output: {result.stdout}")
        print(f"Error: {result.stderr}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Installe intelligemment un package pip avec fallback DNS si besoin.")
    parser.add_argument("package", help="Nom du package à installer")
    parser.add_argument("--force-fallback", action="store_true", help="Forcer l'utilisation de la résolution DNS interne (pas de gethostbyname)")
    args = parser.parse_args()

    success = smart_pip_install(args.package, force_fallback=args.force_fallback)
    sys.exit(0 if success else 1)

