import os
import subprocess
import time
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, "venv", "bin", "python3")
PYTHON_EXEC = VENV_PYTHON if os.path.exists(VENV_PYTHON) else "python3"

SUPERVISORS = [
    "echo_supervisor_1.py",
    "echo_supervisor_2.py",
    "echo_supervisor_3.py"
]
CORE = "core.py"
LOG_FILE = os.path.join(BASE_DIR, "logs", "launcher.log")
PID_FILE = os.path.join(BASE_DIR, "logs", "core.pid")


def log(msg):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")


def lancer_processus(script_name):
    script_path = os.path.join(BASE_DIR, script_name)
    subprocess.Popen(
        [PYTHON_EXEC, script_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=BASE_DIR
    )
    log(f"Lancement de {script_name}")


def lancer_core():
    core_path = os.path.join(BASE_DIR, CORE)
    proc = subprocess.Popen(
        [PYTHON_EXEC, core_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=BASE_DIR
    )
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))
    log(f"Lancement de {CORE} (PID: {proc.pid})")


def monitor_core():
    while True:
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # Check if process still alive
        except Exception:
            log(f"{CORE} s’est arrêté ! Redémarrage...")
            lancer_core()
        time.sleep(10)


if __name__ == "__main__":
    log("Launcher démarré")
    for sup in SUPERVISORS:
        lancer_processus(sup)
        time.sleep(0.5)
    lancer_core()
    monitor_core()

