# Imagen base ligera de Python
FROM python:3.9-slim

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && \
    apt-get install -y curl tzdata && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Configurar zona horaria Bogotá
ENV TZ=America/Bogota
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar la aplicación
COPY . .

# Descargar Supercronic correcto y dar permisos
RUN curl -L -o /usr/local/bin/supercronic \
    https://github.com/aptible/supercronic/releases/download/v0.2.29/supercronic-linux-amd64 \
    && chmod +x /usr/local/bin/supercronic


# Copiar start.sh y dar permisos
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Copiar crontab
COPY crontab /app/crontab

# Exponer el puerto de Flask
EXPOSE 8080

# Ejecutar start.sh como entrypoint
CMD ["/app/start.sh"]
