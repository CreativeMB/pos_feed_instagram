# Usa una imagen base oficial de Python
FROM python:3.9-slim-buster

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo requirements.txt primero para aprovechar el cache de Docker
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de tu aplicación al directorio de trabajo
# Esto incluye app.py, encabezados.txt, hashtags.txt y la carpeta texts/
COPY . .

# Comando para ejecutar tu script cuando el contenedor se inicie
# Asegúrate de que 'app.py' sea el nombre de tu script principal
CMD ["python", "app.py"]
