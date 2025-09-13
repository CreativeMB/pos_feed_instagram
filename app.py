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
GOOGLE_DRIVE_JSON_URL = "https://drive.google.com/uc?export=download&id=1mGqnHpLxP3mWUPHVUyJtSb9WiwRlaQ_C" # URL del JSON con las URLs de las imágenes

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
    """
    Carga las URLs de las fotos desde un archivo JSON alojado en Google Drive.
    Asegura que las URLs de las imágenes sean de descarga directa (export=download).
    """
    try:
        response = requests.get(url)
        response.raise_for_status() # Lanza un error para códigos de estado HTTP 4xx/5xx
        data = response.json()
        
        corrected_urls = []
        for key, value_url in data.items():
            # Asegura que la URL sea de descarga directa
            if 'export=view' in value_url:
                corrected_url = value_url.replace('export=view', 'export=download')
                corrected_urls.append(corrected_url)
            elif 'export=download' not in value_url and 'id=' in value_url:
                # Si no tiene export=view ni export=download pero sí id, intenta añadir export=download
                # Esto es una precaución adicional, asumiendo un formato común de ID
                parts = value_url.split('&', 1) # Divide una vez por el primer '&'
                if len(parts) > 1 and parts[0].startswith("https://drive.google.com/uc?"):
                    corrected_url = parts[0] + '&export=download&' + parts[1]
                elif parts[0].startswith("https://drive.google.com/uc?"):
                    corrected_url = parts[0] + '&export=download'
                else: # Si no coincide con el patrón esperado, la añade como está
                    corrected_url = value_url
                corrected_urls.append(corrected_url)
            else:
                corrected_urls.append(value_url) # Ya está en formato de descarga o es otro tipo de URL

        if not corrected_urls:
            raise ValueError("JSON de Google Drive vacío o sin URLs de imagen válidas.")
        
        print(f"URLs de fotos cargadas con éxito. Ejemplo de URL procesada: {corrected_urls[0]}")
        return corrected_urls
    except requests.exceptions.RequestException as req_err:
        print(f"Error de red o HTTP al cargar fotos desde Drive: {req_err}")
        sys.exit(1)
    except json.JSONDecodeError as json_err:
        print(f"Error al decodificar el JSON de Google Drive: {json_err}")
        sys.exit(1)
    except ValueError as val_err:
        print(f"Error de datos en el JSON de Google Drive: {val_err}")
        sys.exit(1)
    except Exception as e:
        print(f"Error inesperado al cargar fotos desde Google Drive: {e}")
        sys.exit(1)

# Se llama a la función corregida
try:
    FOTOS_PUBLICAS_URLS = cargar_fotos_desde_drive(GOOGLE_DRIVE_JSON_URL)
except Exception as e:
    print(f"Terminando la aplicación debido a un error al cargar las fotos: {e}")
    sys.exit(1)


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
        print("Todas las fotos han sido usadas. Reiniciando la lista de fotos usadas.")
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
    # Asegúrate de no intentar tomar más elementos de los que hay disponibles
    h_local = random.sample(HASHTAGS_LOCAL, min(2, len(HASHTAGS_LOCAL))) if HASHTAGS_LOCAL else []
    h_ocas = random.sample(HASHTAGS_OCASION, min(2, len(HASHTAGS_OCASION))) if HASHTAGS_OCASION else []
    h_emoc = random.sample(HASHTAGS_EMOCIONES, min(1, len(HASHTAGS_EMOCIONES))) if HASHTAGS_EMOCIONES else []
    h_gen = random.sample(HASHTAGS_GENERALES, min(2, len(HASHTAGS_GENERALES))) if HASHTAGS_GENERALES else []
    
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
    
    print(f"Intentando crear contenedor de medios con URL: {image_public_url}")
    try:
        response_upload = requests.post(upload_url, params=params_upload)
        response_upload.raise_for_status() # Esto lanzará un HTTPError si la respuesta no es 200 OK
        media_creation_id = response_upload.json()['id']
        print(f"Contenedor de medios creado con ID: {media_creation_id}")
    except requests.exceptions.HTTPError as http_err:
        print(f"Error HTTP al crear contenedor de medios: {http_err}")
        print(f"Respuesta del servidor: {response_upload.text}") # Muestra la respuesta completa para depurar
        return False
    except Exception as e:
        print(f"Error inesperado creando contenedor de medios: {e}")
        return False

    publish_url = f"{graph_url_base}{instagram_account_id}/media_publish"
    params_publish = {'creation_id': media_creation_id, 'access_token': access_token}
    
    print(f"Intentando publicar medio con creation_id: {media_creation_id}")
    try:
        response_publish = requests.post(publish_url, params=params_publish)
        response_publish.raise_for_status()
        print("Medio publicado exitosamente en Instagram.")
        return True
    except requests.exceptions.HTTPError as http_err:
        print(f"Error HTTP al publicar en Instagram: {http_err}")
        print(f"Respuesta del servidor: {response_publish.text}")
        return False
    except Exception as e:
        print(f"Error inesperado publicando en Instagram: {e}")
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
        print(f"Información de la última publicación guardada: {registro['ultima_publicacion']}")

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
                print("Error en la publicación (ver logs anteriores para más detalles).")
        else:
            print("Credenciales de Facebook/Instagram no configuradas. No se puede publicar.")
    except Exception as e:
        print(f"Error general en la tarea programada: {e}")
    finally:
        print(f"--- PUBLICACIÓN FINALIZADA ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")

# -------------------------------
# RUTAS FLASK
# -------------------------------
@app.route('/')
def home():
    return jsonify({
        "status": "activo",
        "ultima_publicacion": registro.get("ultima_publicacion", "N/A"),
        "mensaje": "El bot de publicación de Instagram está en funcionamiento."
    })

@app.route('/publicar_ahora', methods=['GET'])
def trigger_manual_post():
    threading.Thread(target=tarea_programada_publicar_instagram).start()
    return jsonify({
        "status": "ok",
        "message": "Publicación disparada manualmente. Revisa los logs de la aplicación para el estado."
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
