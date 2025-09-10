from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

@app.route("/")
def home():
    return "Servidor de extracción de videos activo ✅"

@app.route("/get-videos", methods=["GET"])
def get_videos():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No se proporcionó URL"}), 400

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        html = r.text

        # Extraer enlaces .mp4, .mkv y .m3u8
        pattern = r"https?:\/\/[^\s'\"<>]+?\.(?:mp4|mkv|m3u8)"
        videos = re.findall(pattern, html)

        if not videos:
            return jsonify({"error": "No se encontraron videos"}), 404

        return jsonify({"videos": videos})
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
