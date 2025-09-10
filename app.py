from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0"}

@app.route("/get-videos", methods=["GET"])
def get_videos():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Falta la URL"}), 400
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        html = resp.text

        # Buscar enlaces de video .mp4, .mkv, .m3u8
        videos = re.findall(r"https?://[^\s'\"]+\.(?:mp4|mkv|m3u8)", html)
        videos = list(dict.fromkeys(videos))  # quitar duplicados manteniendo orden

        return jsonify({"videos": videos})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error al conectar: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
