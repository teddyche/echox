# core/core_pip_manager.py

import importlib.util
import os

# Chargement dynamique de smart_pip.py
SMART_PIP_PATH = os.path.join("installers", "smart_pip.py")
spec = importlib.util.spec_from_file_location("smart_pip", SMART_PIP_PATH)
smart_pip = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smart_pip)

def install_package(package_name, force_fallback=False):
    """
    Tente d’installer un package pip.
    Utilise la méthode classique, puis fallback si nécessaire (ou forçage activé).
    """
    print(f"[🔧 Echo-X::PipManager] Installation demandée pour : {package_name}")
    try:
        success = smart_pip.smart_pip_install(package_name, force_fallback=force_fallback)
        if success:
            print(f"[✅ Echo-X::PipManager] {package_name} installé avec succès.")
        else:
            print(f"[❌ Echo-X::PipManager] Échec d’installation de {package_name}.")
        return success
    except Exception as e:
        print(f"[⚠️ Echo-X::PipManager] Erreur pendant l’installation : {e}")
        return False

# Test manuel (facultatif)
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python core_pip_manager.py <package_name> [--force]")
    else:
        pkg = sys.argv[1]
        force = "--force" in sys.argv
        install_package(pkg, force_fallback=force)

