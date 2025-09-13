from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import random
import json
import os
from datetime import datetime
import requests
import sys
import threading
from flask import Flask, jsonify
import pytz

app = Flask(__name__)

# -------------------------------
# CONFIGURACIÓN
# -------------------------------
REGISTRO_ARCHIVO = "registro_publicaciones.json"
WHATSAPP = "3014418502"
WEB = "www.floristerialoslirios.com"
CIUDAD = "Bogotá"
NEGOCIO = "Floristería Los Lirios"
GOOGLE_DRIVE_JSON_URL = "https://drive.google.com/uc?export=download&id=1mGqnHpLxP3mWUPHVUyJtSb9WiwRlaQ_C"

try:
    FACEBOOK_PAGE_ACCESS_TOKEN = os.environ["FACEBOOK_PAGE_ACCESS_TOKEN"]
    INSTAGRAM_BUSINESS_ACCOUNT_ID = os.environ["INSTAGRAM_BUSINESS_ACCOUNT_ID"]
except KeyError as e:
    print(f"Error CRÍTICO: La variable de entorno {e} no está configurada.")
    sys.exit(1)

# -------------------------------
# CARGAR FOTOS DESDE GOOGLE DRIVE
# -------------------------------
def cargar_fotos_desde_drive(url):
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    urls = list(data.values())
    if not urls:
        raise ValueError("JSON de Google Drive vacío")
    return urls

FOTOS_PUBLICAS_URLS = cargar_fotos_desde_drive(GOOGLE_DRIVE_JSON_URL)

# -------------------------------
# CARGAR REGISTRO
# -------------------------------
if os.path.exists(REGISTRO_ARCHIVO):
    with open(REGISTRO_ARCHIVO, "r", encoding="utf-8") as f:
        registro = json.load(f)
else:
    registro = {"fotos_usadas": [], "textos_usados": [], "hashtags_usados": []}
    with open(REGISTRO_ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=4)

# -------------------------------
# FUNCIONES DE SELECCIÓN DE CONTENIDO
# -------------------------------
def elegir_foto():
    disponibles = list(set(FOTOS_PUBLICAS_URLS) - set(registro.get("fotos_usadas", [])))
    if not disponibles:
        registro["fotos_usadas"] = []
        disponibles = FOTOS_PUBLICAS_URLS
    seleccion = random.choice(disponibles)
    registro["fotos_usadas"].append(seleccion)
    return seleccion

def cargar_lista(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error cargando {path}: {e}")
        sys.exit(1)

ENCABEZADOS = cargar_lista("encabezados.txt")
HASHTAGS_TODOS = cargar_lista("hashtags.txt")

def filtrar_hashtags(categoria):
    return [h.split("|")[0] for h in HASHTAGS_TODOS if h.endswith(f"|{categoria}")]

HASHTAGS_LOCAL = filtrar_hashtags("local")
HASHTAGS_OCASION = filtrar_hashtags("ocasión")
HASHTAGS_EMOCIONES = filtrar_hashtags("emociones")
HASHTAGS_GENERALES = filtrar_hashtags("generales")

def elegir_encabezado():
    seleccion = random.choice(ENCABEZADOS)
    return seleccion.replace("{ciudad}", CIUDAD)

def elegir_hashtags():
    h_local = random.sample(HASHTAGS_LOCAL, min(2, len(HASHTAGS_LOCAL)))
    h_ocas = random.sample(HASHTAGS_OCASION, min(2, len(HASHTAGS_OCASION)))
    h_emoc = random.sample(HASHTAGS_EMOCIONES, min(1, len(HASHTAGS_EMOCIONES)))
    h_gen = random.sample(HASHTAGS_GENERALES, min(2, len(HASHTAGS_GENERALES)))
    combinados = h_local + h_ocas + h_emoc + h_gen
    random.shuffle(combinados)
    return combinados

# -------------------------------
# PUBLICACIÓN EN INSTAGRAM
# -------------------------------
def publicar_en_instagram(instagram_account_id, access_token, image_public_url, caption):
    graph_url_base = "https://graph.facebook.com/v19.0/"
    upload_url = f"{graph_url_base}{instagram_account_id}/media"
    params_upload = {
        'image_url': image_public_url,
        'caption': caption,
        'access_token': access_token
    }
    try:
        response_upload = requests.post(upload_url, params=params_upload)
        response_upload.raise_for_status()
        media_creation_id = response_upload.json()['id']
    except Exception as e:
        print(f"Error creando contenedor de medios: {e}")
        return False

    publish_url = f"{graph_url_base}{instagram_account_id}/media_publish"
    params_publish = {'creation_id': media_creation_id, 'access_token': access_token}
    try:
        response_publish = requests.post(publish_url, params=params_publish)
        response_publish.raise_for_status()
        return True
    except Exception as e:
        print(f"Error publicando en Instagram: {e}")
        return False

# -------------------------------
# FUNCIÓN PRINCIPAL DE PUBLICACIÓN
# -------------------------------
def tarea_programada_publicar_instagram():
    print(f"\n--- INICIANDO PUBLICACIÓN ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
    try:
        foto_url = elegir_foto()
        encabezado = elegir_encabezado()
        hashtags = elegir_hashtags()
        texto_post = f"{encabezado}\nOrdena ya por WhatsApp {WHATSAPP}\n{WEB}\n" + " ".join(hashtags)

        registro["ultima_publicacion"] = {
            "foto": foto_url,
            "encabezado": encabezado,
            "hashtags": hashtags,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(REGISTRO_ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(registro, f, ensure_ascii=False, indent=4)

        if FACEBOOK_PAGE_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID:
            exito = publicar_en_instagram(
                instagram_account_id=INSTAGRAM_BUSINESS_ACCOUNT_ID,
                access_token=FACEBOOK_PAGE_ACCESS_TOKEN,
                image_public_url=foto_url,
                caption=texto_post
            )
            if exito:
                print("Publicación exitosa.")
            else:
                print("Error en la publicación.")
        else:
            print("Credenciales no configuradas.")
    except Exception as e:
        print(f"Error en la tarea programada: {e}")
    finally:
        print(f"--- PUBLICACIÓN FINALIZADA ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")

# -------------------------------
# RUTAS FLASK
# -------------------------------
@app.route('/')
def home():
    return jsonify({
        "status": "activo",
        "ultima_publicacion": registro.get("ultima_publicacion", "N/A")
    })

@app.route('/publicar_ahora', methods=['GET'])
def trigger_manual_post():
    threading.Thread(target=tarea_programada_publicar_instagram).start()
    return jsonify({
        "status": "ok",
        "message": "Publicación disparada. Revisa los logs."
    }), 202

# -------------------------------
# SCHEDULER CON CRON TRIGGER
# -------------------------------
scheduler = BackgroundScheduler()
# Publicación diaria a las 8:10 PM hora Colombia
scheduler.add_job(
    tarea_programada_publicar_instagram,
    trigger=CronTrigger(hour=20, minute=10, timezone=pytz.timezone("America/Bogota")),
    id='instagram_daily_post',
    name='Publicación diaria a las 8:10 PM (hora Colombia)',
    replace_existing=True
)
scheduler.start()
print("Scheduler iniciado. La publicación diaria está programada a las 8:10 PM hora Colombia.")

# -------------------------------
# INICIO DEL SERVIDOR FLASK
# -------------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    print(f"Iniciando servidor Flask en 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
