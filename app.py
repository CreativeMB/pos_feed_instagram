from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Expresiones regulares para videos
VIDEO_REGEX = re.compile(r'(https?:\/\/[^\s"\']+\.(?:mp4|m3u8|mkv))', re.IGNORECASE)

@app.route('/')
def home():
    return "Video Extractor API está corriendo"

@app.route('/get-videos', methods=['GET'])
def get_videos():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Falta parámetro 'url'"}), 400

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        response = requests.get(url, headers=headers, timeout=10)
        html = response.text

        # Buscar todos los enlaces de video en el HTML
        videos = VIDEO_REGEX.findall(html)
        videos = list(set(videos))  # eliminar duplicados

        return jsonify({"videos": videos})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
