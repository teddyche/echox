import os
import time
import subprocess
from datetime import datetime

SUP_NAME = "echo_supervisor_2"
TARGET = "launcher.py"
PID_FILE = f"logs/{SUP_NAME}.pid"
LOG_FILE = f"logs/{SUP_NAME}.log"
PYTHON_EXEC = os.path.abspath("venv/bin/python3")
LAUNCHER_PATH = os.path.abspath("launcher.py")

os.makedirs("logs", exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[🛠] {msg}")

def launcher_actif():
    try:
        output = subprocess.check_output(["pgrep", "-f", LAUNCHER_PATH]).decode().splitlines()
        return any(str(os.getpid()) != pid for pid in output)
    except:
        return False

def relancer_launcher():
    subprocess.Popen(
        [PYTHON_EXEC, LAUNCHER_PATH],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    log(f"{SUP_NAME} relance launcher.py")

def boucle():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    log(f"{SUP_NAME} démarré")
    while True:
        if not launcher_actif():
            relancer_launcher()
        time.sleep(10)

if __name__ == "__main__":
    boucle()

