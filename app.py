import random
import json
import os
from datetime import datetime
import requests
import sys
import threading
import time

# Importamos Flask para crear un servidor web ligero
from flask import Flask, jsonify

# Importamos APScheduler para programar la tarea de publicación
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

app = Flask(__name__)

# -------------------------------
# CONFIGURACIÓN
# -------------------------------
# FOTOS_CARPETA ya no se usará, pero la mantengo si la usas para otras cosas.
REGISTRO_ARCHIVO = "registro_publicaciones.json"

WHATSAPP = "3014418502"
WEB = "www.floristerialoslirios.com"
CIUDAD = "Bogotá"
NEGOCIO = "Floristería Los Lirios"

# --- Configuración de Google Drive JSON ---
GOOGLE_DRIVE_JSON_URL = "https://drive.google.com/uc?export=download&id=1mGqnHpLxP3mWUPHVUyJtSb9WiwRlaQ_C"

# --- Configuración de Facebook/Instagram API (LEYENDO DE SECRETS) ---
# Usamos os.environ[] para que el script falle si estas variables no están configuradas,
# asegurando que los secrets de Fly.io sean obligatorios.
try:
    FACEBOOK_PAGE_ACCESS_TOKEN = os.environ["FACEBOOK_PAGE_ACCESS_TOKEN"]
    INSTAGRAM_BUSINESS_ACCOUNT_ID = os.environ["INSTAGRAM_BUSINESS_ACCOUNT_ID"]
except KeyError as e:
    print(f"Error CRÍTICO: La variable de entorno {e} no está configurada. Por favor, define tus secrets en Fly.io.")
    sys.exit(1) # Salir si los secrets no están definidos.

# -------------------------------
# CARGAR FOTOS (¡AHORA DESDE GOOGLE DRIVE!)
# -------------------------------
def cargar_fotos_desde_drive(url):
    try:
        print(f"Cargando JSON de fotos desde Google Drive: {url}")
        response = requests.get(url)
        response.raise_for_status() # Lanza un error para códigos de estado HTTP incorrectos
        json_data = response.json()
        
        image_urls = list(json_data.values())
        
        if not image_urls:
            raise ValueError("El JSON de Google Drive no contiene URLs de fotos válidas.")
        print(f"Se cargaron {len(image_urls)} URLs de fotos desde Drive.")
        return image_urls
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con Google Drive: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error al decodificar el JSON de Google Drive: {e}")
        raise
    except Exception as e:
        print(f"Error inesperado al cargar fotos desde Drive: {e}")
        raise

# Sustituimos la carga local por la carga desde Drive
try:
    FOTOS_PUBLICAS_URLS = cargar_fotos_desde_drive(GOOGLE_DRIVE_JSON_URL)
except Exception as e:
    print(f"El script no puede continuar sin fotos. Error: {e}")
    sys.exit(1) # Salir si no se pueden cargar las fotos

# -------------------------------
# CARGAR REGISTRO DE PUBLICACIONES
# -------------------------------
# Asegurarse de que REGISTRO_ARCHIVO se pueda crear o leer
try:
    if os.path.exists(REGISTRO_ARCHIVO):
        with open(REGISTRO_ARCHIVO, "r", encoding="utf-8") as f:
            registro = json.load(f)
        print(f"Registro de publicaciones cargado desde {REGISTRO_ARCHIVO}")
    else:
        registro = {"fotos_usadas": [], "textos_usados": [], "hashtags_usados": []}
        with open(REGISTRO_ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(registro, f, ensure_ascii=False, indent=4)
        print(f"Nuevo archivo de registro creado en {REGISTRO_ARCHIVO}")
except Exception as e:
    print(f"ADVERTENCIA: No se pudo cargar o crear el archivo de registro {REGISTRO_ARCHIVO}. El seguimiento de fotos usadas no funcionará. Error: {e}")
    registro = {"fotos_usadas": [], "textos_usados": [], "hashtags_usados": []}


# -------------------------------
# CARGAR ENCABEZADOS Y HASHTAGS DESDE ARCHIVOS (¡Rutas corregidas a la raíz!)
# -------------------------------
def cargar_lista(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: Archivo no encontrado en la ruta: {path}")
        sys.exit(1) # Detener el script si no encuentra los archivos críticos
    except Exception as e:
        print(f"Error al cargar {path}: {e}")
        sys.exit(1)

ENCABEZADOS = cargar_lista("encabezados.txt")
HASHTAGS_TODOS = cargar_lista("hashtags.txt")

# -------------------------------
# FILTRAR HASHTAGS POR CATEGORÍA
# Se asume formato: #tag|categoria
# Ejemplo en hashtags.txt: #FloresBogotá|local
# -------------------------------
def filtrar_hashtags(categoria):
    return [h.split("|")[0] for h in HASHTAGS_TODOS if h.endswith(f"|{categoria}")]

HASHTAGS_LOCAL = filtrar_hashtags("local")
HASHTAGS_OCASION = filtrar_hashtags("ocasión")
HASHTAGS_EMOCIONES = filtrar_hashtags("emociones")
HASHTAGS_GENERALES = filtrar_hashtags("generales")

# -------------------------------
# FUNCIONES DE SELECCIÓN DE CONTENIDO
# -------------------------------
def elegir_foto():
    # 'FOTOS_PUBLICAS_URLS' ahora contiene las URLs directas
    disponibles = list(set(FOTOS_PUBLICAS_URLS) - set(registro.get("fotos_usadas", [])))
    if not disponibles:
        print("Todas las fotos han sido usadas. Reiniciando la lista de fotos usadas.")
        registro["fotos_usadas"] = []
        disponibles = FOTOS_PUBLICAS_URLS
    seleccion = random.choice(disponibles)
    registro["fotos_usadas"].append(seleccion)
    return seleccion # Retorna la URL de la imagen

def elegir_encabezado():
    seleccion = random.choice(ENCABEZADOS)
    return seleccion.replace("{ciudad}", CIUDAD)

def elegir_hashtags():
    # Asegurarse de que haya suficientes hashtags para seleccionar
    h_local = random.sample(HASHTAGS_LOCAL, min(2, len(HASHTAGS_LOCAL)))
    h_ocas = random.sample(HASHTAGS_OCASION, min(2, len(HASHTAGS_OCASION)))
    h_emoc = random.sample(HASHTAGS_EMOCIONES, min(1, len(HASHTAGS_EMOCIONES)))
    h_gen = random.sample(HASHTAGS_GENERALES, min(2, len(HASHTAGS_GENERALES)))
    
    combinados = h_local + h_ocas + h_emoc + h_gen
    random.shuffle(combinados)
    return combinados

# -------------------------------
# LÓGICA DE PUBLICACIÓN DE INSTAGRAM
# -------------------------------
def publicar_en_instagram(instagram_account_id, access_token, image_public_url, caption):
    graph_url_base = "https://graph.facebook.com/v19.0/" # Puedes actualizar a la versión más reciente (ej. v20.0)

    # Paso 1: Subir la imagen y crear el contenedor de medios
    upload_url = f"{graph_url_base}{instagram_account_id}/media"
    
    params_upload = {
        'image_url': image_public_url, # ¡image_public_url ya es la URL pública!
        'caption': caption,
        'access_token': access_token
    }

    print(f"\n[Instagram Publisher] Intentando crear contenedor de medios para Instagram con URL: {image_public_url}...")
    try:
        response_upload = requests.post(upload_url, params=params_upload)
        response_upload.raise_for_status()
        media_creation_id = response_upload.json()['id']
        print(f"[Instagram Publisher] Contenedor de medios creado con éxito. ID: {media_creation_id}")
    except requests.exceptions.HTTPError as err:
        print(f"[Instagram Publisher] ERROR HTTP al crear contenedor de medios en Instagram: {err}")
        if response_upload.text:
            print(f"[Instagram Publisher] Respuesta detallada de Instagram: {response_upload.json()}")
        return False # Fallo en la subida
    except Exception as e:
        print(f"[Instagram Publisher] Ocurrió un error inesperado al crear contenedor de medios: {e}")
        return False

    # Paso 2: Publicar la imagen usando el creation_id
    publish_url = f"{graph_url_base}{instagram_account_id}/media_publish"
    params_publish = {
        'creation_id': media_creation_id,
        'access_token': access_token
    }

    print("[Instagram Publisher] Intentando publicar en Instagram...")
    try:
        response_publish = requests.post(publish_url, params=params_publish)
        response_publish.raise_for_status()
        print(f"[Instagram Publisher] Publicación exitosa en Instagram: {response_publish.json()}")
        return True # Éxito en la publicación
    except requests.exceptions.HTTPError as err:
        print(f"[Instagram Publisher] ERROR HTTP al publicar en Instagram: {err}")
        if response_publish.text:
            print(f"[Instagram Publisher] Respuesta detallada de Instagram: {response_publish.json()}")
        return False
    except Exception as e:
        print(f"[Instagram Publisher] Ocurrió un error inesperado al publicar en Instagram: {e}")
        return False

# -------------------------------
# FUNCIÓN PRINCIPAL DE PUBLICACIÓN DIARIA
# -------------------------------
def tarea_programada_publicar_instagram():
    print(f"\n--- INICIANDO TAREA PROGRAMADA DE PUBLICACIÓN EN INSTAGRAM ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
    
    try:
        foto_url = elegir_foto()
        encabezado = elegir_encabezado()
        hashtags = elegir_hashtags()
        texto_post = f"{encabezado}\nMás de 20 años de experiencia en {CIUDAD}. Ordena ya por WhatsApp {WHATSAPP}\n{WEB}\n" + " ".join(hashtags)

        # -------------------------------
        # GUARDAR REGISTRO
        # -------------------------------
        registro["ultima_publicacion"] = {
            "foto": foto_url,
            "encabezado": encabezado,
            "hashtags": hashtags,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(REGISTRO_ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(registro, f, ensure_ascii=False, indent=4)
        print(f"Registro de publicación guardado en {REGISTRO_ARCHIVO}.")

        print("=== FOTO SELECCIONADA (URL) ===")
        print(foto_url)
        print("\n=== TEXTO DEL POST ===")
        print(texto_post)

        # -------------------------------
        # ¡PUBLICAR EN INSTAGRAM!
        # -------------------------------
        if FACEBOOK_PAGE_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID:
            print("\nIntentando publicar en Instagram...")
            publicacion_exitosa = publicar_en_instagram(
                instagram_account_id=INSTAGRAM_BUSINESS_ACCOUNT_ID,
                access_token=FACEBOOK_PAGE_ACCESS_TOKEN,
                image_public_url=foto_url,
                caption=texto_post
            )
            if publicacion_exitosa:
                print("Publicación programada finalizada con ÉXITO.")
            else:
                print("Publicación programada finalizada con ERRORES.")
        else:
            print("ADVERTENCIA: No se pudo publicar. Credenciales de Facebook/Instagram no configuradas.")

    except Exception as e:
        print(f"ERROR FATAL en la tarea programada de publicación: {e}")
    finally:
        print(f"--- TAREA PROGRAMADA FINALIZADA ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")


# -------------------------------
# RUTAS DE FLASK PARA EL SERVIDOR WEB Y ACTIVADOR MANUAL
# -------------------------------
@app.route('/')
def home():
    return jsonify({
        "status": "activo",
        "message": "Servicio de publicación automática de Floristería Los Lirios",
        "ultima_publicacion": registro.get("ultima_publicacion", "N/A")
    })

@app.route('/publicar_ahora', methods=['GET'])
def trigger_manual_post():
    # Para ejecutar la tarea en un hilo separado y no bloquear la solicitud HTTP
    threading.Thread(target=tarea_programada_publicar_instagram).start()
    return jsonify({
        "status": "ok",
        "message": "Publicación disparada. Revisa los logs para el resultado."
    }), 202

# -------------------------------
# INICIO DEL PROGRAMADOR DE TAREAS (APScheduler)
# -------------------------------
scheduler = BackgroundScheduler()
# Programa la tarea para que se ejecute una vez cada 24 horas (ajusta a tus necesidades)
# La primera ejecución será después del intervalo definido una vez que el scheduler se inicie.
# Si quieres que se ejecute inmediatamente al inicio y luego cada 24h, hay que llamarla.

# Ejemplo: Ejecutar cada 24 horas
scheduler.add_job(
    tarea_programada_publicar_instagram,
    trigger=IntervalTrigger(minutes=1), # O days=1, minutes=5 para probar, etc.
    id='instagram_daily_post',
    name='Publicación diaria en Instagram',
    replace_existing=True
)


# Iniciar el scheduler en un hilo separado
scheduler.start()
print("Scheduler iniciado. La publicación diaria en Instagram está programada.")


# -------------------------------
# INICIO DEL SERVIDOR WEB DE FLASK
# -------------------------------
if __name__ == '__main__':
    # Ejecuta la primera publicación al inicio si lo deseas, o deja que el scheduler se encargue.
    # threading.Thread(target=tarea_programada_publicar_instagram).start()
    
    # Fly.io espera que la aplicación escuche en 0.0.0.0:8080
    port = int(os.environ.get("PORT", 8080))
    print(f"Iniciando servidor Flask en 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False) # debug=False para producción
