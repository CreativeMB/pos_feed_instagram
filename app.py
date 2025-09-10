import os
from flask import Flask, request, jsonify
import re
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return "Servidor de extracción de videos activo ✅"

@app.route("/get-videos")
def get_videos():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No se proporcionó URL"})

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        html = r.text

        # Buscar enlaces .mp4, .mkv y .m3u8
        pattern = r"https?://[^\s'\"<>]+?\.(?:mp4|mkv|m3u8)"
        videos = re.findall(pattern, html)
        videos = list(set(videos))  # Eliminar duplicados

        return jsonify({"videos": videos})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
