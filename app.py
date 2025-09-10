from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import requests

app = Flask(__name__)
CORS(app)

@app.route("/get-videos")
def get_videos():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL no proporcionada"}), 400

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        html = r.text
        videos = re.findall(r'https?://[^\s"\']+\.(?:mp4|mkv|m3u8)', html)
        videos = list(set(videos))
        return jsonify({"videos": videos})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


