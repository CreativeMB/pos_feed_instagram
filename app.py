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

# Patrón para videos
VIDEO_PATTERN = r'https?://[^\s"\'>]+?\.(?:mp4|mkv|m3u8)(?:\?[^"\'>\s]*)?'

async def extract_videos(url: str):
    videos = set()
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
        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state("networkidle")
            print("[INFO] Página cargada correctamente")

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

            # 3️⃣ Extraer links de botones o divs con video
            buttons = await page.query_selector_all("a[href], button, div[data-video]")
            for btn in buttons:
                try:
                    href = await btn.get_attribute("href")
                    if href and href.lower().endswith((".mp4", ".mkv", ".m3u8")):
                        videos.add(href)

                    # Intentar click dinámico solo si el botón es visible
                    if await btn.is_visible():
                        await btn.click(timeout=5000)
                        await page.wait_for_load_state("networkidle")
                        content_after = await page.content()
                        for match in re.findall(VIDEO_PATTERN, content_after):
                            if "favicon" not in match.lower():
                                videos.add(match)
                except PlaywrightTimeoutError:
                    print("[WARN] Timeout al hacer click en un botón, se continúa")
                    continue
                except Exception as e:
                    print(f"[WARN] Error al procesar botón: {e}")
                    continue

            # 4️⃣ Extra: Capturar variables JS dinámicas
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

        except PlaywrightTimeoutError:
            print("⚠ Timeout al cargar la página")
        except Exception as e:
            print(f"⚠ Error en extract_videos: {e}")
        finally:
            await browser.close()
            print(f"[INFO] Chromium cerrado. Se encontraron {len(videos)} videos")

    return list(videos)

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
