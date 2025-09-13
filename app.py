import random
import json
import os
from datetime import datetime
import requests
import sys
import threading
from flask import Flask, jsonify
import pytz
from main_app import tarea_programada_publicar_instagram  # Solo la función de publicación
# -------------------------------
# CONFIGURACIÓN
# -------------------------------
REGISTRO_ARCHIVO = "registro_publicaciones.json"
WHATSAPP = "3014418502"
WEB = "www.floristerialoslirios.com"
CIUDAD = "Bogotá"
NEGOCIO = "Floristería Los Lirios"

# Configuración para imágenes locales
STATIC_IMAGES_FOLDER_NAME = "static" # Nombre de la carpeta estática de Flask
IMAGES_SUB_FOLDER = "images" # Subcarpeta dentro de static para las imágenes
# Ruta completa en el sistema de archivos donde se esperan las imágenes
FULL_STATIC_IMAGES_PATH = os.path.join(STATIC_IMAGES_FOLDER_NAME, IMAGES_SUB_FOLDER)

# Inicializa la aplicación Flask, indicando dónde buscar los archivos estáticos
app = Flask(__name__, static_folder=STATIC_IMAGES_FOLDER_NAME)

try:
    FACEBOOK_PAGE_ACCESS_TOKEN = os.environ["FACEBOOK_PAGE_ACCESS_TOKEN"]
    INSTAGRAM_BUSINESS_ACCOUNT_ID = os.environ["INSTAGRAM_BUSINESS_ACCOUNT_ID"]
    # Variable de entorno para la URL base de la aplicación desplegada
    # EJEMPLO: https://tu-app-de-instagram.fly.dev o https://www.tudominio.com
    APP_BASE_URL = os.environ["APP_BASE_URL"].rstrip('/') # Asegurarse de que no termine con '/'
except KeyError as e:
    print(f"Error CRÍTICO: La variable de entorno {e} no está configurada.")
    print("Asegúrate de definir FACEBOOK_PAGE_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID y APP_BASE_URL.")
    sys.exit(1)

# -------------------------------
# CARGAR FOTOS LOCALES
# -------------------------------
def cargar_fotos_locales(folder_path, app_base_url):
    """
    Carga los nombres de archivo de las fotos desde una carpeta local
    y construye sus URLs públicas absolutas usando la URL base de la aplicación.
    """
    if not os.path.isdir(folder_path):
        print(f"Advertencia: La carpeta de imágenes '{folder_path}' no existe. Intentando crearla.")
        try:
            os.makedirs(folder_path, exist_ok=True) # Crea la carpeta si no existe
            print(f"Carpeta '{folder_path}' creada con éxito.")
        except OSError as e:
            raise RuntimeError(f"No se pudo crear la carpeta de imágenes '{folder_path}': {e}")

    # Extensiones de imagen que se buscarán
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp') 
    
    local_image_files = []
    for f in os.listdir(folder_path):
        file_path = os.path.join(folder_path, f)
        if os.path.isfile(file_path) and f.lower().endswith(image_extensions):
            local_image_files.append(f)

    if not local_image_files:
        raise ValueError(f"No se encontraron imágenes con extensiones {image_extensions} en la carpeta '{folder_path}'.")

    public_urls = []
    for filename in local_image_files:
        # Construye la URL completa. Flask sirve archivos estáticos en el prefijo definido por static_url_path (por defecto '/static/')
        # La URL será: https://APP_BASE_URL/static/images/nombre_imagen.jpg
        full_public_url = f"{app_base_url}/{STATIC_IMAGES_FOLDER_NAME}/{IMAGES_SUB_FOLDER}/{filename}"
        public_urls.append(full_public_url)
    
    print(f"Fotos locales cargadas con éxito desde '{folder_path}'. Total: {len(public_urls)} imágenes.")
    print(f"Ejemplo de URL de imagen procesada: {public_urls[0]}")
    return public_urls

# Se llama a la función para cargar las fotos locales
try:
    FOTOS_PUBLICAS_URLS = cargar_fotos_locales(FULL_STATIC_IMAGES_PATH, APP_BASE_URL)
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
        print(f"Respuesta del servidor (subida): {response_upload.text}") # Muestra la respuesta completa para depurar
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
        print(f"Respuesta del servidor (publicación): {response_publish.text}")
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
        nombre_imagen = os.path.basename(foto_url)
        encabezado = elegir_encabezado()
        hashtags = elegir_hashtags()
        texto_post = f"{encabezado}\nOrdena ya por WhatsApp {WHATSAPP}\n{WEB}\n" + " ".join(hashtags)

        registro["ultima_publicacion"] = {
            "foto": foto_url,
            "nombre_imagen": nombre_imagen,
            "encabezado": encabezado,
            "hashtags": hashtags,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(REGISTRO_ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(registro, f, ensure_ascii=False, indent=4)
        print(f"Información de la última publicación guardada: {registro['ultima_publicacion']}")

        if FACEBOOK_PAGE_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID and APP_BASE_URL:
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
            print("Credenciales o APP_BASE_URL no configurados. No se puede publicar en Instagram.")
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
        "mensaje": "El bot de publicación de Instagram está en funcionamiento y sirve imágenes localmente."
    })

@app.route('/publicar_ahora', methods=['GET'])
def trigger_manual_post():
    threading.Thread(target=tarea_programada_publicar_instagram).start()
    return jsonify({
        "status": "ok",
        "message": "Publicación disparada manualmente. Revisa los logs de la aplicación para el estado."
    }), 202


# -------------------------------
# INICIO DEL SERVIDOR FLASK
# -------------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    print(f"Iniciando servidor Flask en 0.0.0.0:{port}")
    # Usar 'threaded=True' asegura que Flask pueda manejar peticiones mientras el scheduler está activo
    # y el hilo de publicación manual puede ejecutarse.
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
