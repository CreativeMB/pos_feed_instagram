# Imagen base ligera de Python
FROM python:3.9-slim

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y curl tzdata && \
    apt-get clean

# Configurar zona horaria Bogotá
ENV TZ=America/Bogota
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar la aplicación
COPY . .

# Descargar Supercronic y dar permisos
RUN curl -L -o /usr/local/bin/supercronic \
    https://github.com/aptible/supercronic/releases/download/v0.2.4/supercronic-linux-amd64 && \
    chmod +x /usr/local/bin/supercronic

# Dar permisos al script de inicio
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Copiar crontab
COPY crontab /app/crontab

# Exponer el puerto de Flask
EXPOSE 8080

# Ejecutar start.sh
CMD ["/app/start.sh"]
