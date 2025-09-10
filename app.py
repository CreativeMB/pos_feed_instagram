from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route("/get-videos")
def get_videos():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        videos = []

        # Extraer enlaces mp4, mkv, m3u8 de <a> y <source>
        for tag in soup.find_all(["a", "source"], href=True):
            if tag["href"].endswith((".mp4", ".mkv", ".m3u8")):
                videos.append(tag["href"])
        for tag in soup.find_all("source", src=True):
            if tag["src"].endswith((".mp4", ".mkv", ".m3u8")):
                videos.append(tag["src"])

        # Quitar duplicados
        videos = list(set(videos))
        return jsonify({"videos": videos})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
