# app.py
from flask import Flask, jsonify, render_template, request
from main_scheduler import generate_schedule, run_dynamic_reoptimizer
from database import init_db

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")  

@app.route("/api/generate", methods=["POST"])
def api_generate():
    result = generate_schedule()
    return jsonify({"status":"ok","assigned":result})

@app.route("/api/reopt", methods=["POST"])
def api_reopt():
    data = request.get_json(force=True)
    affected = data.get("affected_students", [])
    result = run_dynamic_reoptimizer(affected)
    return jsonify({"status":"ok","assigned":result})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
