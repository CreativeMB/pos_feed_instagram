FROM python:3.9-slim-buster

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiar tu aplicación
COPY . .

# Descargar Supercronic
RUN apt-get update && apt-get install -y curl && \
    curl -L -o /usr/local/bin/supercronic https://github.com/aptible/supercronic/releases/download/v0.2.4/supercronic-linux-amd64 && \
    chmod +x /usr/local/bin/supercronic

# Copiar el archivo de cron
COPY crontab /etc/crontab

# Puerto interno de tu app Flask
EXPOSE 8080

# Comando por defecto: correr supercronic + tu app
CMD supercronic /etc/crontab
