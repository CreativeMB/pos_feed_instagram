from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import asyncio
import os
import nest_asyncio
import urllib.parse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

nest_asyncio.apply()  # Permite correr asyncio dentro de Flask

app = Flask(__name__)
CORS(app)  # Permite solicitudes desde cualquier dominio

VIDEO_PATTERN = r'https?://[^\s"\']+\.(?:mp4|mkv|m3u8)'

async def extract_videos(url: str):
    videos = set()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state("networkidle")

            # Extraer contenido HTML
            content = await page.content()
            videos.update(re.findall(VIDEO_PATTERN, content))

            # Extraer de <video> y <source>
            video_elements = await page.query_selector_all("video")
            for v in video_elements:
                src = await v.get_attribute("src")
                if src: videos.add(src)
                sources = await v.query_selector_all("source")
                for s in sources:
                    ssrc = await s.get_attribute("src")
                    if ssrc: videos.add(ssrc)

            # Extra: enlaces de botones y divs
            server_buttons = await page.query_selector_all("a[href], button[data-video], div[data-video]")
            for btn in server_buttons:
                try:
                    href = await btn.get_attribute("href")
                    if href: videos.update(re.findall(VIDEO_PATTERN, href))
                except:
                    continue

        except PlaywrightTimeoutError:
            print("⚠ Timeout al cargar la página")
        except Exception as e:
            print(f"⚠ Error en extract_videos: {e}")
        finally:
            await browser.close()

    # --- FILTRAR Y CORREGIR URLs ---
    filtered_videos = []
    for v in videos:
        if "google.com/s2/favicons" in v:
            # Extraer el parámetro domain_url si existe
            parsed = urllib.parse.urlparse(v)
            params = urllib.parse.parse_qs(parsed.query)
            if "domain_url" in params:
                real_url = params["domain_url"][0]
                if re.search(r'\.(mp4|mkv|m3u8)', real_url):
                    filtered_videos.append(real_url)
        else:
            if re.search(r'\.(mp4|mkv|m3u8)', v):
                filtered_videos.append(v)

    # Eliminar duplicados
    return list(set(filtered_videos))


@app.route("/get-videos")
def get_videos():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL no proporcionada"}), 400

    try:
        videos = asyncio.run(extract_videos(url))
        if not videos:
            return jsonify({"error": "No se encontraron videos"}), 404
        return jsonify({"videos": videos})
    except Exception as e:
        print(f"⚠ Error en get_videos: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
