# Imagen base mínima con Python
FROM python:3.12-slim

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos necesarios
COPY app.py requirements.txt ./

# Instalar dependencias sin cache
RUN pip install --no-cache-dir -r requirements.txt

# Exponer puerto 8080
EXPOSE 8080

# Comando para iniciar la app
CMD ["python", "app.py"]
