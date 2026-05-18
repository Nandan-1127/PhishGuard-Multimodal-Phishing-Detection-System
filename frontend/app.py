from flask import Flask, render_template, request, jsonify
import requests, json, os, base64
from datetime import datetime

app = Flask(__name__)
BACKEND_URL = "http://127.0.0.1:8000"
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "data.json")

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"history": [], "reported": []}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_history(scan_type, target, result):
    try:
        data = load_data()
        entry = {
            "id": len(data["history"]) + 1,
            "type": scan_type,
            "target": str(target)[:120],
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
        data["history"].insert(0, entry)
        data["history"] = data["history"][:100]
        save_data(data)
    except Exception:
        pass

def get_llava_url():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as ef:
            for line in ef:
                line = line.strip()
                if line.startswith("LLAVA_API_URL="):
                    return line.split("=", 1)[1].strip()
    return ""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/scan/url", methods=["POST"])
def scan_url():
    url = (request.json or {}).get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    try:
        r = requests.post(f"{BACKEND_URL}/scan/url", json={"url": url}, timeout=30)
        result = r.json()
        save_history("url", url, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/scan/email", methods=["POST"])
def scan_email():
    text = (request.json or {}).get("text", "").strip()
    if not text:
        return jsonify({"error": "No email text"}), 400
    try:
        r = requests.post(f"{BACKEND_URL}/scan/email", json={"text": text}, timeout=30)
        result = r.json()
        save_history("email", text[:80], result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/scan/screenshot", methods=["POST"])
def scan_screenshot():
    url = (request.json or {}).get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL"}), 400
    try:
        r = requests.post(f"{BACKEND_URL}/scan/screenshot", json={"url": url}, timeout=90)
        result = r.json()
        save_history("screenshot", url, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/scan/image", methods=["POST"])
def scan_image():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400
        img_b64 = base64.b64encode(file.read()).decode("utf-8")
        llava_url = get_llava_url()
        if not llava_url:
            return jsonify({
                "image_score": None,
                "llava_response": "LLaVA not configured. Set LLAVA_API_URL in .env file.",
                "screenshot_base64": img_b64
            })
        resp = requests.post(
            f"{llava_url}/analyze",
            json={"screenshot_base64": img_b64, "url": "direct-upload"},
            timeout=60
        )
        result = resp.json()
        result["screenshot_base64"] = img_b64
        save_history("image", file.filename, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/scan/qr", methods=["POST"])
def scan_qr():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file"}), 400
        files = {"file": (file.filename, file.read(), file.content_type)}
        r = requests.post(f"{BACKEND_URL}/scan/qr", files=files, timeout=30)
        result = r.json()
        save_history("qr", result.get("qr_url", "QR Code"), result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/history")
def get_history():
    return jsonify(load_data()["history"])

@app.route("/api/history/clear", methods=["POST"])
def clear_history():
    data = load_data()
    data["history"] = []
    save_data(data)
    return jsonify({"ok": True})

@app.route("/api/report", methods=["POST"])
def report_url():
    url = (request.json or {}).get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL"}), 400
    data = load_data()
    if url not in data["reported"]:
        data["reported"].append(url)
        save_data(data)
    return jsonify({"ok": True})

@app.route("/api/check_reported", methods=["POST"])
def check_reported():
    url = (request.json or {}).get("url", "").strip()
    data = load_data()
    return jsonify({"is_reported": url in data["reported"]})

if __name__ == "__main__":
    os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
    app.run(debug=True, port=5000)