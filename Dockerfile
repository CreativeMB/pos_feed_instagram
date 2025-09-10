# Imagen base ligera
FROM python:3.12-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos
COPY app.py requirements.txt ./

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Puerto expuesto por Fly.io
EXPOSE 8080

# Comando de arranque
CMD ["python", "app.py"]
