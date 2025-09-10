from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import requests

app = Flask(__name__)
CORS(app)  # Permite solicitudes desde cualquier dominio

@app.route("/get-videos")
def get_videos():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL no proporcionada"}), 400

    try:
        # Obtenemos el contenido de la página
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        html = r.text

        # Buscamos enlaces de video (.mp4, .mkv, .m3u8)
        videos = re.findall(r'https?://[^\s"\']+\.(?:mp4|mkv|m3u8)', html)
        videos = list(set(videos))  # eliminamos duplicados

        return jsonify({"videos": videos})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
