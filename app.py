import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Servidor de extracción de videos activo ✅"

@app.route("/get-videos")
def get_videos():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No se proporcionó URL"})
    
    # Aquí solo simulamos extracción (en tu versión real pondrías tu código)
    videos = [f"{url}/video1.mp4", f"{url}/video2.m3u8"]
    return jsonify({"videos": videos})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

