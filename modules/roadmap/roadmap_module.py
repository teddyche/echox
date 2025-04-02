import os
import json
from flask import Blueprint, request, render_template_string, redirect, url_for

roadmap_route = Blueprint("roadmap_route", __name__)
ROADMAP_FILE = os.path.join("modules", "roadmap", "roadmap.json")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🗺️ Roadmap Echo-X</title>
    <style>
        body { font-family: sans-serif; background: #121212; color: #eee; padding: 2em; }
        h1 { color: #6cf; }
        ul { list-style: none; padding: 0; }
        li { margin: 0.5em 0; padding: 0.5em; background: #1e1e1e; border-radius: 8px; display: flex; align-items: center; justify-content: space-between; }
        input[type=checkbox] { margin-right: 1em; transform: scale(1.4); }
        form { display: inline; }
        input[type=text] { padding: 0.3em; border-radius: 6px; border: none; width: 300px; }
        button { margin-left: 0.5em; background: #6cf; color: black; font-weight: bold; padding: 0.4em 0.8em; border-radius: 6px; border: none; cursor: pointer; }
        button:hover { background: #88f; color: white; }
        .done { text-decoration: line-through; color: #888; }
    </style>
</head>
<body>
    <h1>🗺️ Roadmap Echo-X</h1>
    <form action="{{ url_for('roadmap_route.add_task') }}" method="post">
        <input type="text" name="task" placeholder="Nouvelle tâche...">
        <button type="submit">➕ Ajouter</button>
    </form>
    <ul>
        {% for item in roadmap %}
        <li>
            <form action="{{ url_for('roadmap_route.toggle_task', index=loop.index0) }}" method="post">
                <input type="checkbox" onchange="this.form.submit()" {% if item.done %}checked{% endif %}>
            </form>
            <span class="{{ 'done' if item.done else '' }}">{{ item.task }}</span>
            <form action="{{ url_for('roadmap_route.delete_task', index=loop.index0) }}" method="post">
                <button>❌</button>
            </form>
        </li>
        {% endfor %}
    </ul>
    <br>
    <a href="/echo_web"><button>⬅️ Retour à Echo-X</button></a>
</body>
</html>
"""

def charger_roadmap():
    if not os.path.exists(ROADMAP_FILE):
        return []
    with open(ROADMAP_FILE, "r") as f:
        return json.load(f)

def sauvegarder_roadmap(data):
    with open(ROADMAP_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@roadmap_route.route("/roadmap", methods=["GET"])
def afficher_roadmap():
    roadmap = charger_roadmap()
    return render_template_string(HTML_TEMPLATE, roadmap=roadmap)

@roadmap_route.route("/roadmap/add", methods=["POST"])
def add_task():
    task = request.form.get("task", "").strip()
    if task:
        roadmap = charger_roadmap()
        roadmap.append({"task": task, "done": False})
        sauvegarder_roadmap(roadmap)
    return redirect(url_for("roadmap_route.afficher_roadmap"))

@roadmap_route.route("/roadmap/toggle/<int:index>", methods=["POST"])
def toggle_task(index):
    roadmap = charger_roadmap()
    if 0 <= index < len(roadmap):
        roadmap[index]["done"] = not roadmap[index]["done"]
        sauvegarder_roadmap(roadmap)
    return redirect(url_for("roadmap_route.afficher_roadmap"))

@roadmap_route.route("/roadmap/delete/<int:index>", methods=["POST"])
def delete_task(index):
    roadmap = charger_roadmap()
    if 0 <= index < len(roadmap):
        roadmap.pop(index)
        sauvegarder_roadmap(roadmap)
    return redirect(url_for("roadmap_route.afficher_roadmap"))

