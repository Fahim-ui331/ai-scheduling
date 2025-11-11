# ==========================
#  app.py (Final Fixed Version)
# ==========================

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename
import os

# Import your project modules
from seed_from_csv import seed_all
from main_scheduler import generate_schedule, run_dynamic_reoptimizer
from database import init_db

# ✅ 1. Create Flask app BEFORE using routes
app = Flask(__name__, static_folder='static', template_folder='templates')

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ✅ 2. Now define all your routes
@app.route("/")
def home():
    return render_template("index.html")  # optional, only if you have index.html

@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Run the schedule generator."""
    result = generate_schedule()
    return jsonify({"status": "ok", "assigned": result})

@app.route("/api/reopt", methods=["POST"])
def api_reopt():
    """Run re-optimizer for specific students."""
    data = request.get_json(force=True)
    affected = data.get("affected_students", [])
    result = run_dynamic_reoptimizer(affected)
    return jsonify({"status": "ok", "assigned": result})

@app.route("/admin/upload-csv", methods=["POST"])
def upload_csv():
    """Upload and seed CSV files into the database."""
    saved = {}
    for key in ["students", "courses", "sections", "prefs"]:
        file = request.files.get(key)
        if file:
            path = os.path.join(UPLOAD_DIR, secure_filename(file.filename))
            file.save(path)
            saved[key] = path

    if not saved:
        return jsonify({"status": "error", "message": "No files uploaded"}), 400

    seed_all(
        students_csv=saved.get("students"),
        courses_csv=saved.get("courses"),
        sections_csv=saved.get("sections"),
        prefs_csv=saved.get("prefs"),
    )
    return jsonify({"status": "ok", "seeded_files": list(saved.keys())})

# ✅ 3. Finally, run the Flask app
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
