import os
import re
from datetime import datetime

from flask import Flask, abort, jsonify, render_template, request

app = Flask(__name__)

PROJECTS_DIR = os.path.join(os.path.dirname(__file__), "projects")
MAX_CONTENT_BYTES = 100 * 1024  # 100KB
MAX_NAME_LENGTH = 64
VALID_NAME_RE = re.compile(r"^[a-z0-9_-]+$")


def _sanitize_name(raw: str) -> str:
    """Lowercase, strip whitespace, replace spaces with hyphens."""
    name = raw.strip().lower().replace(" ", "-")
    return name


def _validate_name(name: str) -> str | None:
    """Return an error string if the name is invalid, else None."""
    if not name:
        return "Project name is required."
    if len(name) > MAX_NAME_LENGTH:
        return f"Project name must be {MAX_NAME_LENGTH} characters or fewer."
    if not VALID_NAME_RE.match(name):
        return "Project name may only contain lowercase letters, numbers, hyphens, and underscores."
    return None


def _validate_content(content: str) -> str | None:
    """Return an error string if the content is invalid, else None."""
    if len(content.encode("utf-8")) > MAX_CONTENT_BYTES:
        return "Content exceeds the 100 KB limit."
    return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/save", methods=["POST"])
def save():
    raw_name = request.form.get("name", "")
    raw_content = request.form.get("content", "")

    name = _sanitize_name(raw_name)

    name_error = _validate_name(name)
    if name_error:
        return jsonify({"error": name_error}), 400

    # Strip null bytes from content
    content = raw_content.replace("\x00", "")

    content_error = _validate_content(content)
    if content_error:
        return jsonify({"error": content_error}), 400

    os.makedirs(PROJECTS_DIR, exist_ok=True)
    filepath = os.path.join(PROJECTS_DIR, f"{name}.md")

    if os.path.exists(filepath):
        return jsonify({"error": f"'{name}.md' already exists. Choose a different name."}), 409

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        app.logger.error("Failed to write file: %s", e)
        return jsonify({"error": "Server error: could not save file."}), 500

    return jsonify({"message": f"'{name}.md' saved successfully."}), 200


@app.route("/list")
def list_projects():
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    files = []
    for fname in sorted(os.listdir(PROJECTS_DIR)):
        if fname.endswith(".md"):
            fpath = os.path.join(PROJECTS_DIR, fname)
            mtime = os.path.getmtime(fpath)
            files.append({
                "name": fname,
                "modified": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
            })
    return render_template("list.html", files=files)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5111, debug=False)
