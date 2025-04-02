# tools/core_pip_manager.py

import importlib
import sys
import os

# Chemin vers smart_pip.py (s'il est dans tools/installers/)
SMART_PIP_PATH = os.path.join(os.path.dirname(__file__), "installers", "smart_pip.py")

if not os.path.exists(SMART_PIP_PATH):
    raise FileNotFoundError(f"smart_pip.py introuvable ici: {SMART_PIP_PATH}")

import importlib.util
spec = importlib.util.spec_from_file_location("smart_pip", SMART_PIP_PATH)
smart_pip = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smart_pip)


def check_package(pkg):
    """Vérifie si un module est importable."""
    try:
        importlib.import_module(pkg)
        return True
    except ImportError:
        return False


def install_if_missing(pkg, fallback=False):
    """Installe le module s'il est manquant."""
    if not check_package(pkg):
        print(f"[⚠️ Echo-X] Package '{pkg}' manquant. Tentative d'installation...")
        success = smart_pip.smart_pip_install(pkg, force_fallback=fallback)
        if success:
            print(f"[✅ Echo-X] '{pkg}' installé avec succès.")
            return True
        else:
            print(f"[❌ Echo-X] Échec d'installation de '{pkg}'.")
            return False
    return True


def ensure_critical_dependencies(packages, fallback=False):
    """Vérifie et installe les dépendances critiques."""
    print("[🔍 Echo-X] Vérification des dépendances critiques...")
    all_ok = True
    for pkg in packages:
        ok = install_if_missing(pkg, fallback=fallback)
        if not ok:
            all_ok = False
    return all_ok

