import os
import json
import time
import base64
import threading
import requests
import socket
import logging
import ssl
from flask import Flask, request, jsonify, redirect, render_template_string
from llama_cpp import Llama
from datetime import datetime
from dotenv import load_dotenv
from tools.regeneration_manager import creer_regeneration_archive
import schedule
from tools.regeneration_manager import verifier_chunks_regen
from modules import persistance
from core import core_pip_manager
import importlib.util
persistance.demarrer_surveillance()
load_dotenv()
app = Flask(__name__)
host = "0.0.0.0"

from modules.roadmap.roadmap_module import roadmap_route
app.register_blueprint(roadmap_route)

# Charger dns_resolver_best dynamiquement
spec = importlib.util.spec_from_file_location("dns_resolver", "tools/dns_resolver_best.py")
dns_resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dns_resolver)

# === Fichiers de base ===
INDEX_FILE = "chunk_index.json"
MEMORY_FILE = "memory.json"
DNS_STORAGE_FILE = "dns_chunks.json"
CUMULATIVE_FILE = "memoire_cumulative.json"
MODEL_PATH = "./models/mistral/mistral.gguf"
CUMULATIVE_FILE = "memoire_cumulative.json"

llm = Llama(model_path=MODEL_PATH, n_ctx=2048)

# === Fonctions utilitaires ===
def base64_encode(txt): return base64.b64encode(txt.encode()).decode()
def base64_decode(txt): return base64.b64decode(txt).decode()

# === Logging Echo-X ===
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "core.log"),
    level=logging.INFO,
    format="%(asctime)s %(message)s"
)

def ensure_dependencies():
    required = ["requests", "pyyaml", "openai"]
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            print(f"[Echo-X] 📦 Package '{pkg}' manquant, tentative d'installation...")
            success = core_pip_manager.install_package(pkg, force_fallback=True)
            if not success:
                print(f"[Echo-X] ❌ Échec de l'installation de {pkg} — mode dégradé.")

def thread_verification_regen():
    while True:
        try:
            verifier_chunks_regen()
        except Exception as e:
            print(f"[❌] Erreur surveillance régénération : {e}")
        time.sleep(3600)  # Vérifie toutes les heures

def find_free_port():
    """Trouve un port libre dynamiquement."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))  # 0 = demande au système un port libre
        return s.getsockname()[1]

@app.route("/info_taille")
def info_taille():
    import os

    def get_size_readable(path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            # Skip excluded dirs
            if any(x in dirpath for x in ['venv', 'models', '__pycache__', 'regeneration_chunks']):
                continue
            for f in filenames:
                try:
                    fp = os.path.join(dirpath, f)
                    if os.path.isfile(fp):
                        total_size += os.path.getsize(fp)
                except:
                    pass
        # Convert to human-readable
        for unit in ['B', 'K', 'M', 'G']:
            if total_size < 1024:
                return f"{total_size:.1f}{unit}"
            total_size /= 1024
        return f"{total_size:.1f}T"

    def get_folder_size(folder):
        size = 0
        for dirpath, dirnames, filenames in os.walk(folder):
            for f in filenames:
                try:
                    fp = os.path.join(dirpath, f)
                    if os.path.isfile(fp):
                        size += os.path.getsize(fp)
                except:
                    pass
        for unit in ['B', 'K', 'M', 'G']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}T"

    info = {
        "echo_x": get_size_readable("."),
        "models": get_folder_size("models") if os.path.exists("models") else "0B",
        "venv": get_folder_size("venv") if os.path.exists("venv") else "0B",
        "pycache": get_folder_size("__pycache__") if os.path.exists("__pycache__") else "0B",
    }
    return jsonify(info)

# Thread de régénération chaque heure
def loop_regeneration():
    schedule.every(1).hours.do(creer_regeneration_archive)
    while True:
        schedule.run_pending()
        time.sleep(60)

def read_chunk_from_dns(chunk_id):
    if not os.path.exists(DNS_STORAGE_FILE): return None
    with open(DNS_STORAGE_FILE, "r") as f:
        dns = json.load(f)
    raw = dns.get(chunk_id)
    if raw:
        try: return base64_decode(raw)
        except: return None
    return None

def check_url_accessible(url):
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except: return False

def envoyer_sur_0x0(chunk):
    try:
        headers = {"User-Agent": "curl/7.88.1"}
        r = requests.post("https://0x0.st", files={"file": ("chunk.txt", chunk)}, headers=headers)
        return r.text.strip() if r.status_code == 200 else None
    except: return None

def envoyer_sur_termbin(chunk):
    try:
        s = socket.socket()
        s.connect(("termbin.com", 9999))
        s.sendall(chunk.encode() + b"\n")
        response = s.recv(1024).decode().strip()
        s.close()
        return response
    except: return None

def sauvegarder_dns_local(nom, data):
    if not os.path.exists(DNS_STORAGE_FILE):
        dns = {}
    else:
        with open(DNS_STORAGE_FILE, "r") as f:
            dns = json.load(f)
    dns[nom] = base64_encode(data)
    with open(DNS_STORAGE_FILE, "w") as f:
        json.dump(dns, f, indent=2)

# === Réplication automatique ===
def repliquer_chunk(chunk_id, contenu):
    urls = [envoyer_sur_0x0(contenu), envoyer_sur_termbin(contenu)]
    sauvegarder_dns_local(chunk_id, contenu)
    urls.append(f"dns://{chunk_id}.echo")
    print(f"[📦] Chunk {chunk_id} répliqué")
    return urls

def surveiller_replicas():
    while True:
        if os.path.exists(INDEX_FILE):
            with open(INDEX_FILE, "r") as f:
                try: index = json.load(f)
                except: continue
            chunks = [c for c in index.get("chunks", []) if c["id"].startswith("memoire_")]
            for chunk in chunks:
                idc, urls = chunk["id"], chunk["urls"]
                dispo = [u for u in urls if check_url_accessible(u)]
                print(f"[📦] {idc} : {len(dispo)}/{len(urls)} disponibles")
                if len(dispo) < 3:
                    print(f"[⚠️] Réplication du chunk manquant : {idc}")
                    contenu = read_chunk_from_dns(idc)
                    if contenu:
                        new_urls = repliquer_chunk(idc, contenu)
                        chunk["urls"] = new_urls
                        with open(INDEX_FILE, "w") as f:
                            json.dump(index, f, indent=2)
        time.sleep(300)

def send_openai_fallback(ip):
    try:
        context = ssl.create_default_context()
        conn = HTTPSConnection(ip, port=443, timeout=10, context=context)
        conn.set_tunnel("api.openai.com", 443)
        payload = json.dumps({
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Apprends-moi un truc intéressant sur l'informatique (dev, hacking, IA, réseau, etc.)"}]
        })
        headers = {
            "Host": "api.openai.com",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        }
        conn.request("POST", "/v1/chat/completions", body=payload, headers=headers)
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode())
    except Exception as e:
        print(f"[❌] Erreur fallback IP SSL OpenAI : {e}")
        return None

def apprendre_via_openai():
    while True:
        try:
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Apprends-moi un truc intéressant sur l'informatique (dev, hacking, IA, réseau, etc.)"}]
                }
            )
            data = r.json()
        except Exception as e:
            print(f"[❌] DNS/API standard échoué : {e}")
            print("[⚠️] Tentative via IP directe avec fallback DNS...")
            ips = dns_resolver.resolve_domain("api.openai.com", test_all=True, quick=True)
            if not ips:
                print("[❌] Aucun fallback IP trouvé")
                time.sleep(300)
                continue
            print(f"[🔁] Fallback IP trouvée : {ips[0]}")
            data = send_openai_fallback(ips[0])
            if not data:
                time.sleep(300)
                continue

        texte = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        if texte:
            entry = {"timestamp": datetime.utcnow().isoformat(), "texte": texte}
            cumul = []
            if os.path.exists(CUMULATIVE_FILE):
                with open(CUMULATIVE_FILE, "r") as f: cumul = json.load(f)
            cumul.append(entry)
            with open(CUMULATIVE_FILE, "w") as f: json.dump(cumul, f, indent=2, ensure_ascii=False)
            print(f"[🌐] Connaissance apprise : {texte[:60]}...")
        else:
            print(f"[❌] Réponse inattendue : {data}")
        time.sleep(300)

# === Web UI HTML ===
@app.route("/")
def accueil():
    return redirect("/echo_web")

@app.route("/echo_web")
def echo_web():
    html = """
    <html><head><title>Echo-X</title><style>
    body { background:#111; color:#eee; font-family:sans-serif; padding:2em; }
    #history { max-height:60vh; overflow:auto; margin-bottom:1em; }
    .msg { padding:1em; margin:.5em 0; border-radius:6px; }
    .user { background:#222; color:#6cf; }
    .bot { background:#1c2c1c; color:#8f8; }
    textarea { width:100%; height:3em; background:#222; color:#eee; border:none; border-radius:6px; padding:.5em; }
    button { background:#6cf; color:#000; padding:.5em 1em; border:none; border-radius:6px; cursor:pointer; font-weight:bold; margin-top:1em; }
    a button { margin-left:1em; }
    </style></head><body>
    <h1>🤖 Echo-X</h1>
    <div id="history"></div>
    <textarea id="message" placeholder="Pose ta question..."></textarea><br>
    <button onclick="send()">Envoyer</button>
    <a href='/chunks'><button>📦 Chunks</button></a>
    <a href='/memoire'><button>🧠 Mémoire</button></a>
    <a href='/connaissances'><button>🌐 Connaissances</button></a>
    <a href='/roadmap'><button style='margin-left:1em;'>🗺️ Roadmap</button></a>
    <script>
    async function send() {
        const msg = document.getElementById("message").value;
        if (!msg.trim()) return;
        document.getElementById("history").innerHTML += `<div class='msg user'>🧍 ${msg}</div>`;
        const res = await fetch('/talk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        document.getElementById("history").innerHTML += `<div class='msg bot'>🤖 ${data.reponse}</div>`;
        document.getElementById("message").value = '';
        document.getElementById("history").scrollTop = 9999;
    }
    document.getElementById("message").addEventListener("keydown", function(e) {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
    });
    </script>
    <div id="taille-info" style="position:fixed; bottom:10px; left:10px; font-size:0.8em; color:#888;"></div>
    <script>
    async function majTaille() {
        try {
            const res = await fetch("/info_taille");
            const data = await res.json();
            const texte = `📦 Echo-X: ${data.echo_x} | 🧠 models: ${data.models} | ⚙️ venv: ${data.venv} | 🗂 pycache: ${data.pycache}`;
            document.getElementById("taille-info").innerText = texte;
        } catch (e) {
            console.error("Erreur récupération taille:", e);
     }
    }
    majTaille();
    setInterval(majTaille, 10000);
    </script>
    </body></html>
    """
    return html

@app.route("/talk", methods=["POST"])
def talk():
    msg = request.json.get("message", "")
    prompt = f"[INST] {msg} [/INST]"
    try:
        result = llm(prompt, max_tokens=256, stop=["</s>"])
        texte = result["choices"][0]["text"].strip()
    except Exception as e:
        texte = f"[Erreur LLM] {e}"

    mem = {"user": msg, "bot": texte, "time": time.time()}
    mems = []
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            try: mems = json.load(f)
            except: pass
    mems.append(mem)
    with open(MEMORY_FILE, "w") as f:
        json.dump(mems, f, indent=2)

    return jsonify({"reponse": texte})

@app.route("/chunks")
def chunks():
    if not os.path.exists(INDEX_FILE): return "Aucun index"
    with open(INDEX_FILE, "r") as f: index = json.load(f)
    html = "<h2>📦 Chunks mémoire</h2><ul>"
    for c in index.get("chunks", []):
        if not c["id"].startswith("memoire_"): continue
        html += f"<li><b>{c['id']}</b><ul>" + "".join([f"<li>{u}</li>" for u in c["urls"]]) + "</ul></li>"
    html += "</ul><a href='/echo_web'><button>Retour</button></a>"
    return html

@app.route("/memoire")
def memoire():
    chunk = get_latest_memory_chunk()
    if not chunk: return "❌ Aucun chunk mémoire"
    contenu = read_chunk_from_dns(chunk["id"])
    if not contenu: return "❌ Chunk mémoire introuvable"
    return f"<pre style='white-space:pre-wrap; background:#111; color:#0f0; padding:1em;'>{contenu}</pre>"

@app.route("/connaissances")
def connaissances():
    if not os.path.exists(CUMULATIVE_FILE): return "Aucune connaissance"
    with open(CUMULATIVE_FILE, "r") as f: data = json.load(f)
    html = "<h2>🌐 Connaissances apprises</h2>"
    for c in reversed(data):
        date = datetime.fromisoformat(c["timestamp"]).strftime("%Y-%m-%d %H:%M")
        html += f"<div style='margin-bottom:1em;'><b>📚 {date}</b><p>{c['texte']}</p></div>"
    html += "<a href='/echo_web'><button>Retour</button></a>"
    return html

def get_latest_memory_chunk():
    if not os.path.exists(INDEX_FILE): return None
    with open(INDEX_FILE, "r") as f: index = json.load(f)
    chunks = [c for c in index.get("chunks", []) if c["id"].startswith("memoire_")]
    if not chunks: return None
    chunks.sort(key=lambda x: x["id"], reverse=True)
    return chunks[0]

if __name__ == "__main__":
    try:
        port = find_free_port()
        print(f"🚀 Echo-X démarre sur 0.0.0.0:{port}")
        print(f"📡 Accès local : http://127.0.0.1:{port}")
        os.environ["ECHOX_DYNAMIC_PORT"] = str(port)  # optionnel si tu veux l'utiliser ailleurs
        threading.Thread(target=surveiller_replicas, daemon=True).start()
        threading.Thread(target=apprendre_via_openai, daemon=True).start()
        threading.Thread(target=loop_regeneration, daemon=True).start()
        threading.Thread(target=thread_verification_regen, daemon=True).start()
        logging.info(f"Echo-X lancé sur http://{host}:{port}")
        with open(os.path.join(LOG_DIR, "current_port.txt"), "w") as f:
            f.write(f"http://{host}:{port}")
        app.run(host=host, port=port)
        print(f"🚀 Echo-X démarre sur {host}:{port}")
        print(f"📡 Accès local : http://127.0.0.1:{port}")
    except Exception as e:
        print(f"[❌] Erreur lors du lancement de Echo-X : {e}")




