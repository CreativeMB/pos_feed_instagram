# Imagen ligera de Python
FROM python:3.12-slim

# Crear carpeta de la app
WORKDIR /app

# Copiar dependencias primero (mejor caché)
COPY requirements.txt .

# Instalar dependencias con pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la app
COPY app.py .

# Exponer puerto que Fly.io asignará
EXPOSE 8080

# Usar Gunicorn para producción
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app", "--workers=2", "--threads=2"]
