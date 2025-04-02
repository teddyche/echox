import os
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime

LAUNCHER_PATH = os.path.abspath("launcher.py")
LOG_PATH = os.path.join("logs", "persistence.log")
CHECK_INTERVAL = 1800  # 30 minutes

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs("logs", exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[🛡️] {message}")

def ajouter_bashrc():
    bashrc = os.path.expanduser("~/.bashrc")
    ligne = f"python3 {LAUNCHER_PATH} &\n"
    with open(bashrc, "r") as f:
        contenu = f.read()
    if ligne.strip() not in contenu:
        with open(bashrc, "a") as f:
            f.write(f"\n# Echo-X auto-start\n{ligne}")
        log("Ajouté à ~/.bashrc")

def ajouter_crontab():
    try:
        resultat = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        lignes = resultat.stdout.splitlines() if resultat.returncode == 0 else []
        cmd = f"@reboot python3 {LAUNCHER_PATH}"
        if cmd not in lignes:
            lignes.append(cmd)
            temp = "\n".join(lignes) + "\n"
            subprocess.run(["crontab", "-"], input=temp, text=True)
            log("Ajouté à crontab")
    except Exception as e:
        log(f"Erreur crontab : {e}")

def est_lance():
    result = subprocess.run(["pgrep", "-f", LAUNCHER_PATH], capture_output=True, text=True)
    pids = [pid for pid in result.stdout.splitlines() if pid and int(pid) != os.getpid()]
    return len(pids) > 0

def relancer_si_necessaire():
    if not est_lance():
        subprocess.Popen(["python3", LAUNCHER_PATH])
        log("Launcher relancé automatiquement")

def boucle_surveillance():
    while True:
        try:
            ajouter_bashrc()
            ajouter_crontab()
            relancer_si_necessaire()
        except Exception as e:
            log(f"Erreur boucle persistance : {e}")
        time.sleep(CHECK_INTERVAL)

def demarrer_surveillance():
    t = threading.Thread(target=boucle_surveillance, daemon=True)
    t.start()
    log("Surveillance persistance activée")

