from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

@app.route('/extract', methods=['POST'])
def extract():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = r.text

        # Buscar enlaces .mp4, .mkv, .m3u8
        links = re.findall(r'https?://[^\s"\']+\.(?:mp4|mkv|m3u8)', html)
        return jsonify({'links': links})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
