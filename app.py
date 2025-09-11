# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import asyncio
import os
import nest_asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

nest_asyncio.apply()

app = Flask(__name__)
CORS(app)

VIDEO_PATTERN = r'https?://[^\s"\'>]+?\.(?:mp4|mkv|m3u8)(?:\?[^"\'>\s]*)?'

async def extract_videos(url: str):
    videos = set()
    visited_iframes = set()

    print(f"[INFO] Iniciando extracción para: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--disable-gpu",
                "--disable-software-rasterizer"
            ]
        )
        page = await browser.new_page()

        # Capturar todas las requests de video
        page.on("response", lambda response: asyncio.create_task(check_video_response(response, videos)))

        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state("networkidle")
            print("[INFO] Página cargada correctamente")

            await extract_from_page(page, videos, visited_iframes)

        except PlaywrightTimeoutError:
            print("⚠ Timeout al cargar la página")
        except Exception as e:
            print(f"⚠ Error en extract_videos: {e}")
        finally:
            await browser.close()
            print(f"[INFO] Chromium cerrado. Se encontraron {len(videos)} videos")

    return list(videos)


async def check_video_response(response, videos):
    url = response.url
    if re.search(r'\.(mp4|mkv|m3u8)(\?.*)?$', url):
        print(f"[INFO] Video detectado en request: {url}")
        videos.add(url)


async def extract_from_page(page, videos, visited_iframes):
    # 1️⃣ Extraer enlaces directos desde HTML
    content = await page.content()
    for match in re.findall(VIDEO_PATTERN, content):
        if "favicon" not in match.lower():
            videos.add(match)

    # 2️⃣ Extraer <video> y <source>
    video_elements = await page.query_selector_all("video")
    for v in video_elements:
        src = await v.get_attribute("src")
        if src and "favicon" not in src.lower():
            videos.add(src)
        sources = await v.query_selector_all("source")
        for s in sources:
            ssrc = await s.get_attribute("src")
            if ssrc and "favicon" not in ssrc.lower():
                videos.add(ssrc)

    # 3️⃣ Extraer iframes y recorrerlos
    iframe_elements = await page.query_selector_all("iframe")
    for iframe in iframe_elements:
        src = await iframe.get_attribute("src")
        if src and src not in visited_iframes and "twitter.com" not in src:
            visited_iframes.add(src)
            print(f"[INFO] Iframe detectado: {src}")
            try:
                iframe_page = await page.context.new_page()
                await iframe_page.goto(src, timeout=30000)
                await iframe_page.wait_for_load_state("networkidle")
                await extract_from_page(iframe_page, videos, visited_iframes)
                await iframe_page.close()
            except Exception as e:
                print(f"[WARN] Error al procesar iframe: {e}")

    # 4️⃣ Extra: Variables JS dinámicas
    try:
        js_video = await page.evaluate("""
            () => {
                const vars = [];
                for(const key in window) {
                    if(typeof window[key] === 'string' && window[key].match(/\\.mkv$|\\.mp4$|\\.m3u8$/)) {
                        vars.push(window[key]);
                    }
                }
                return vars;
            }
        """)
        if js_video:
            videos.update(js_video)
    except Exception:
        pass


@app.route("/get-videos")
def get_videos():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL no proporcionada"}), 400
    try:
        loop = asyncio.get_event_loop()
        videos = loop.run_until_complete(extract_videos(url))
        if not videos:
            return jsonify({"error": "No se encontraron videos"}), 404
        return jsonify({"videos": videos})
    except Exception as e:
        print(f"⚠ Error en get_videos: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
