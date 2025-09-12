import random
import json
import os
from datetime import datetime

# -------------------------------
# CONFIGURACIÓN
# -------------------------------
FOTOS_CARPETA = "fotos"
REGISTRO_ARCHIVO = "registro_publicaciones.json"

WHATSAPP = "3014418502"
WEB = "www.floristerialoslirios.com"
CIUDAD = "Bogotá"
NEGOCIO = "Floristería Los Lirios"


FACEBOOK_PAGE_ACCESS_TOKEN = "EAAVhavBM6PwBPQ2ZCcgJVZA2eaZCCe2yf2KzghgZCKsL7SoG4Oc4cFqEYa1fDmcftL1z5VXUKcpPt0GbZABEboEYKQLcDKw3scI985zVTgmo8ISYQENOndGuUGPGqG8Ezfwy42S2YUinaOXDPwVwpaZBpbggOguE2ou6enET1m6jDKZBZCt059PJNX4JqCBwftoeLvo3Xt7fpFsiDi7z7HnDUN72mBDgP5rHJp5vP4j7NDgZD"
# Lo obtendrás siguiendo los pasos que te di con el Graph API Explorer:
# me/accounts -> buscar tu Page ID.
# Luego {page-id}?fields=instagram_business_account -> copiar el 'id' de la respuesta.
INSTAGRAM_BUSINESS_ACCOUNT_ID = "17841402134241308"

# -------------------------------
# CARGAR FOTOS
# -------------------------------
fotos = [f for f in os.listdir(FOTOS_CARPETA) if f.lower().endswith((".jpg", ".png"))]
if not fotos:
    raise ValueError("No se encontraron fotos en la carpeta.")

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
HASHTAGS_EMOCIONES = filtrar_hashtags("emociones")
HASHTAGS_GENERALES = filtrar_hashtags("generales")

# -------------------------------
# FUNCIONES
# -------------------------------
def elegir_foto():
    disponibles = list(set(fotos) - set(registro.get("fotos_usadas", [])))
    if not disponibles:
        registro["fotos_usadas"] = []
        disponibles = fotos
    seleccion = random.choice(disponibles)
    registro["fotos_usadas"].append(seleccion)
    return seleccion

def elegir_encabezado():
    seleccion = random.choice(ENCABEZADOS)
    return seleccion.replace("{ciudad}", CIUDAD)

def elegir_hashtags():
    h_local = random.sample(HASHTAGS_LOCAL, min(2, len(HASHTAGS_LOCAL)))
    h_ocas = random.sample(HASHTAGS_OCASION, min(2, len(HASHTAGS_OCASION)))
    h_emoc = random.sample(HASHTAGS_EMOCIONES, min(1, len(HASHTAGS_EMOCIONES)))
    h_gen  = random.sample(HASHTAGS_GENERALES, min(2, len(HASHTAGS_GENERALES)))
    combinados = h_local + h_ocas + h_emoc + h_gen
    random.shuffle(combinados)
    return combinados

# -------------------------------
# GENERAR POST
# -------------------------------
foto = elegir_foto()
encabezado = elegir_encabezado()
hashtags = elegir_hashtags()
texto_post = f"{encabezado}\nMás de 20 años de experiencia en {CIUDAD}. Ordena ya por WhatsApp {WHATSAPP}\n{WEB}\n" + " ".join(hashtags)

# -------------------------------
# GUARDAR REGISTRO
# -------------------------------
registro_guardar = registro.copy()
registro_guardar["ultima_publicacion"] = {
    "foto": foto,
    "encabezado": encabezado,
    "hashtags": hashtags,
    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}
with open(REGISTRO_ARCHIVO, "w", encoding="utf-8") as f:
    json.dump(registro_guardar, f, ensure_ascii=False, indent=4)

# -------------------------------
# GUARDAR JSON PARA CREATOR STUDIO / API
# -------------------------------
post_data = {
    "foto": os.path.join(FOTOS_CARPETA, foto),
    "texto": texto_post
}
with open("post_del_dia.json", "w", encoding="utf-8") as f:
    json.dump(post_data, f, ensure_ascii=False, indent=4)

# -------------------------------
# MOSTRAR RESULTADO
# -------------------------------
print("=== FOTO SELECCIONADA ===")
print(foto)
print("\n=== TEXTO DEL POST ===")
print(texto_post)
