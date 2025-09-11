from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import asyncio
import os
import nest_asyncio
from playwright.async_api import async_playwright

# Permite ejecutar asyncio dentro de Flask
nest_asyncio.apply()

app = Flask(__name__)
CORS(app)  # Permite solicitudes desde cualquier dominio

VIDEO_PATTERN = r'https?://[^\s"\']+\.(?:mp4|mkv|m3u8)'

async def extract_videos(url: str):
    async with async_playwright() as p:
        # Chromium sin sandbox para Fly
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=30000)  # Espera máximo 30s
            content = await page.content()
            # Extraer links de video
            videos = re.findall(VIDEO_PATTERN, content)
            return list(set(videos))  # Eliminar duplicados
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
    # Puerto que Fly asigna
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
