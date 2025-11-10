# app.py (add this part near the top of your routes)
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from seed_from_csv import seed_all  # <-- your seeding script

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/admin/upload-csv", methods=["POST"])
def upload_csv():
    """
    Upload and seed CSV files into the database.
    Accepts multipart/form-data with keys:
        students, courses, sections, prefs
    Example (frontend or Postman):
        POST /admin/upload-csv
        Form-Data:
            students -> students.csv
            courses  -> courses.csv
            sections -> sections.csv
            prefs    -> prefs.csv
    """
    saved = {}

    # loop through possible upload keys
    for key in ["students", "courses", "sections", "prefs"]:
        file = request.files.get(key)
        if file:
            path = os.path.join(UPLOAD_DIR, secure_filename(file.filename))
            file.save(path)
            saved[key] = path

    if not saved:
        return jsonify({"status": "error", "message": "No files uploaded"}), 400

    # seed everything into DB
    seed_all(
        students_csv=saved.get("students"),
        courses_csv=saved.get("courses"),
        sections_csv=saved.get("sections"),
        prefs_csv=saved.get("prefs"),
    )

    return jsonify({"status": "ok", "seeded_files": list(saved.keys())})
