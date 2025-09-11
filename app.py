from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re

app = Flask(__name__)
CORS(app)

@app.route("/get-videos")
def get_videos():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL no proporcionada"}), 400

    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Esperar un momento para que JS cargue los videos
        driver.implicitly_wait(5)
        
        html = driver.page_source
        driver.quit()

        # Extraer enlaces de video
        videos = re.findall(r'https?://[^\s"\']+\.(?:mp4|mkv|m3u8)', html)
        videos = list(set(videos))

        return jsonify({"videos": videos})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)



