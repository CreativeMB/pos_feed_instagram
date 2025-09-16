# 1️⃣ Imagen base ligera de Python
FROM python:3.9-slim

# 2️⃣ Configurar directorio de trabajo
WORKDIR /app

# 3️⃣ Instalar dependencias de sistema necesarias + tzdata
RUN apt-get update && \
    apt-get install -y curl tzdata && \
    ln -snf /usr/share/zoneinfo/America/Bogota /etc/localtime && \
    echo "America/Bogota" > /etc/timezone && \
    apt-get clean

# 4️⃣ Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5️⃣ Copiar la aplicación
COPY . .

# 6️⃣ Descargar Supercronic
RUN curl -L -o /usr/local/bin/supercronic https://github.com/aptible/supercronic/releases/download/v0.2.4/supercronic-linux-amd64 \
    && chmod +x /usr/local/bin/supercronic

# 7️⃣ Copiar el crontab
COPY crontab /app/crontab

# 8️⃣ Exponer el puerto de Flask
EXPOSE 8080

# 9️⃣ Ejecutar Supercronic + Flask usando shell
CMD ["sh", "-c", "supercronic /app/crontab & python app.py"]
