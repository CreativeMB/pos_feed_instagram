from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import asyncio
from playwright.async_api import async_playwright

app = Flask(__name__)
CORS(app)  # Permite solicitudes desde cualquier dominio

VIDEO_PATTERN = r'https?://[^\s"\']+\.(?:mp4|mkv|m3u8)'

async def extract_videos(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=30000)  # Espera máximo 30s
            content = await page.content()

            # Extraer links de video
            videos = re.findall(VIDEO_PATTERN, content)
            videos = list(set(videos))  # Eliminar duplicados
            return videos
        finally:
            await browser.close()

@app.route("/get-videos")
def get_videos():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL no proporcionada"}), 400

    try:
        videos = asyncio.run(extract_videos(url))
        return jsonify({"videos": videos})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)




