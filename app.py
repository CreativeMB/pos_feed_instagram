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
CORS(app)

# Patrón para capturar videos .mp4, .mkv, .m3u8
VIDEO_PATTERN = r'https?://[^\s"\']+\.(?:mp4|mkv|m3u8)'

async def extract_videos(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        try:
            # Ir a la URL y esperar a que se cargue completamente JS
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state("networkidle")  # Espera a que termine JS
            content = await page.content()
            
            # Buscar links de video en el DOM final
            videos = re.findall(VIDEO_PATTERN, content)
            
            # También podemos buscar en elementos <video> y sus fuentes
            video_elements = await page.query_selector_all("video")
            for v in video_elements:
                src = await v.get_attribute("src")
                if src:
                    videos.append(src)
                # Revisar <source> dentro de <video>
                sources = await v.query_selector_all("source")
                for s in sources:
                    ssrc = await s.get_attribute("src")
                    if ssrc:
                        videos.append(ssrc)
            
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
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

