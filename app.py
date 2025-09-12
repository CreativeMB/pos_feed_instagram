import random
import json
import os
from datetime import datetime
import requests # ¡Asegúrate de tener instalada esta librería: pip install requests!

# -------------------------------
# CONFIGURACIÓN
# -------------------------------
FOTOS_CARPETA = "fotos" # Esta carpeta ya no se usará para listar, pero la mantengo si la usas para otras cosas.
REGISTRO_ARCHIVO = "registro_publicaciones.json"

WHATSAPP = "3014418502"
WEB = "www.floristerialoslirios.com"
CIUDAD = "Bogotá"
NEGOCIO = "Floristería Los Lirios"

# --- Configuración de Google Drive JSON ---
# URL del JSON alojado en Google Drive. Asegúrate de que el archivo esté compartido "Cualquier persona con el enlace".
GOOGLE_DRIVE_JSON_URL = "https://drive.google.com/uc?export=download&id=1mGqnHpLxP3mWUPHVUyJtSb9WiwRlaQ_C"

# --- Configuración de Facebook/Instagram API ---
FACEBOOK_PAGE_ACCESS_TOKEN = "EAAVhavBM6PwBPQ2ZCcgJVZA2eaZCCe2yf2KzghgZCKsL7SoG4Oc4cFqEYa1fDmcftL1z5VXUKcpPt0GbZABEboEYKQLcDKw3scI985zVTgmo8ISYQENOndGuUGPGqG8Ezfwy42S2YUinaOXDPwVwpaZBpbggOguE2ou6enET1m6jDKZBZCt059PJNX4JqCBwftoeLvo3Xt7fpFsiDi7z7HnDUN72mBDgP5rHJp5vP4j7NDgZD"
INSTAGRAM_BUSINESS_ACCOUNT_ID = "17841402134241308"


# -------------------------------
# CARGAR FOTOS (¡AHORA DESDE GOOGLE DRIVE!)
# -------------------------------
def cargar_fotos_desde_drive(url):
    try:
        response = requests.get(url)
        response.raise_for_status() # Lanza un error para códigos de estado HTTP incorrectos
        json_data = response.json()
        
        # Asumo que el JSON es un objeto donde los valores son las URLs de las fotos
        # Ejemplo: {"foto1": "http://url.com/foto1.jpg", "foto2": "http://url.com/foto2.png"}
        # Si tu JSON es una lista directa de URLs: ["http://url1.jpg", "http://url2.png"],
        # entonces 'list(json_data.values())' debería ser simplemente 'json_data'.
        
        # Si el JSON es un diccionario de objetos con una clave 'url':
        # {"item1": {"nombre": "Foto 1", "url": "http://url.com/foto1.jpg"}, ...}
        # entonces sería [item['url'] for item in json_data.values()]
        
        # Para el ejemplo 'referenciasDrive[key] = json.getString(key)', asumimos
        # que es un diccionario simple { "clave": "url_de_la_imagen" }
        image_urls = list(json_data.values())
        
        if not image_urls:
            raise ValueError("El JSON de Google Drive no contiene URLs de fotos válidas.")
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
    fotos = cargar_fotos_desde_drive(GOOGLE_DRIVE_JSON_URL)
except Exception as e:
    print(f"El script no puede continuar sin fotos. Error: {e}")
    exit()

# -------------------------------
# CARGAR REGISTRO DE PUBLICACIONES
# -------------------------------
if os.path.exists(REGISTRO_ARCHIVO):
    with open(REGISTRO_ARCHIVO, "r", encoding="utf-8") as f:
        registro = json.load(f)
else:
    registro = {"fotos_usadas": [], "textos_usados": [], "hashtags_usados": []}

# -------------------------------
# CARGAR ENCABEZADOS Y HASHTAGS DESDE ARCHIVOS
# -------------------------------
def cargar_lista(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

ENCABEZADOS = cargar_lista("texts/encabezados.txt")
HASHTAGS_TODOS = cargar_lista("texts/hashtags.txt")

# -------------------------------
# FILTRAR HASHTAGS POR CATEGORÍA
# Se asume formato: #tag|categoria
# Ejemplo en hashtags.txt: #FloresBogotá|local
# -------------------------------
def filtrar_hashtags(categoria):
    return [h.split("|")[0] for h in HASHTAGS_TODOS if h.endswith(f"|{categoria}")]

HASHTAGS_LOCAL = filtrar_hashtags("local")
HASHTAGS_OCASION = filtrar_hashtags("ocasión")
HASHTAGS_EMOCIONES = filtrar_hashtags(
    "emociones"
)
HASHTAGS_GENERALES = filtrar_hashtags("generales")

# -------------------------------
# FUNCIONES
# -------------------------------
def elegir_foto():
    # 'fotos' ahora contiene las URLs directas
    disponibles = list(set(fotos) - set(registro.get("fotos_usadas", [])))
    if not disponibles:
        registro["fotos_usadas"] = []
        disponibles = fotos
    seleccion = random.choice(disponibles)
    registro["fotos_usadas"].append(seleccion)
    return seleccion # Retorna la URL de la imagen

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

# --- Función para publicar en Instagram Feed ---
def publicar_en_instagram(instagram_account_id, access_token, image_public_url, caption):
    graph_url_base = "https://graph.facebook.com/v19.0/" # Puedes actualizar a la versión más reciente (ej. v20.0)

    # Paso 1: Subir la imagen y crear el contenedor de medios
    upload_url = f"{graph_url_base}{instagram_account_id}/media"
    
    params_upload = {
        'image_url': image_public_url, # ¡Ahora 'foto' ya es la URL pública!
        'caption': caption,
        'access_token': access_token
    }

    print(f"\nIntentando crear contenedor de medios para Instagram con URL: {image_public_url}...")
    try:
        response_upload = requests.post(upload_url, params=params_upload)
        response_upload.raise_for_status() # Lanza un error para códigos de estado HTTP incorrectos (4xx o 5xx)
        media_creation_id = response_upload.json()['id']
        print(f"Contenedor de medios creado con éxito. ID: {media_creation_id}")
    except requests.exceptions.HTTPError as err:
        print(f"ERROR HTTP al crear contenedor de medios en Instagram: {err}")
        if response_upload.text:
            print(f"Respuesta detallada de Instagram: {response_upload.json()}")
        return
    except Exception as e:
        print(f"Ocurrió un error inesperado al crear contenedor de medios: {e}")
        return

    # Paso 2: Publicar la imagen usando el creation_id
    publish_url = f"{graph_url_base}{instagram_account_id}/media_publish"
    params_publish = {
        'creation_id': media_creation_id,
        'access_token': access_token
    }

    print("Intentando publicar en Instagram...")
    try:
        response_publish = requests.post(publish_url, params=params_publish)
        response_publish.raise_for_status()
        print("Publicación exitosa en Instagram:", response_publish.json())
    except requests.exceptions.HTTPError as err:
        print(f"ERROR HTTP al publicar en Instagram: {err}")
        if response_publish.text:
            print(f"Respuesta detallada de Instagram: {response_publish.json()}")
    except Exception as e:
        print(f"Ocurrió un error inesperado al publicar en Instagram: {e}")


# -------------------------------
# GENERAR POST
# -------------------------------
# 'foto' ahora contendrá directamente la URL de la imagen de Drive
foto_url = elegir_foto()
encabezado = elegir_encabezado()
hashtags = elegir_hashtags()
texto_post = f"{encabezado}\nMás de 20 años de experiencia en {CIUDAD}. Ordena ya por WhatsApp {WHATSAPP}\n{WEB}\n" + " ".join(hashtags)

# -------------------------------
# GUARDAR REGISTRO
# -------------------------------
registro_guardar = registro.copy()
registro_guardar["ultima_publicacion"] = {
    "foto": foto_url, # Guardamos la URL en el registro
    "encabezado": encabezado,
    "hashtags": hashtags,
    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}
with open(REGISTRO_ARCHIVO, "w", encoding="utf-8") as f:
    json.dump(registro_guardar, f, ensure_ascii=False, indent=4)

# -------------------------------
# GUARDAR JSON PARA CREATOR STUDIO / API (y preparar para el envío)
# -------------------------------
post_data = {
    "foto": foto_url, # La ruta local ya no es necesaria aquí, ahora es la URL pública
    "texto": texto_post
}
with open("post_del_dia.json", "w", encoding="utf-8") as f:
    json.dump(post_data, f, ensure_ascii=False, indent=4)

# -------------------------------
# MOSTRAR RESULTADO
# -------------------------------
print("=== FOTO SELECCIONADA (URL) ===")
print(foto_url)
print("\n=== TEXTO DEL POST ===")
print(texto_post)

# -------------------------------
# ¡PUBLICAR EN INSTAGRAM!
# -------------------------------
if INSTAGRAM_BUSINESS_ACCOUNT_ID != "TU_ID_DE_CUENTA_DE_INSTAGRAM_BUSINESS_AQUI":
    print("\n=== INTENTANDO PUBLICAR EN INSTAGRAM ===")
    publicar_en_instagram(
        instagram_account_id=INSTAGRAM_BUSINESS_ACCOUNT_ID,
        access_token=FACEBOOK_PAGE_ACCESS_TOKEN,
        image_public_url=post_data["foto"], # Pasamos la URL directamente
        caption=post_data["texto"]
    )
else:
    print("\nADVERTENCIA: No se pudo publicar en Instagram. Por favor, asegúrate de que el 'INSTAGRAM_BUSINESS_ACCOUNT_ID' esté configurado correctamente.")
