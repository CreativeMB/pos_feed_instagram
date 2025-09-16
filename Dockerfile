# 1️⃣ Imagen base ligera de Python
FROM python:3.9-slim

# 2️⃣ Configurar directorio de trabajo
WORKDIR /app

# 3️⃣ Instalar dependencias de sistema necesarias
RUN apt-get update && \
    apt-get install -y curl tzdata && \
    apt-get clean

# 4️⃣ Establecer la zona horaria Bogotá
ENV TZ=America/Bogota
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 5️⃣ Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6️⃣ Copiar la aplicación
COPY . .

# 7️⃣ Descargar Supercronic y dar permisos
RUN curl -L -o /usr/local/bin/supercronic https://github.com/aptible/supercronic/releases/download/v0.2.4/supercronic-linux-amd64 && \
    chmod +x /usr/local/bin/supercronic

# 8️⃣ Copiar crontab y dar permisos al script start.sh
COPY crontab /app/crontab
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 9️⃣ Exponer el puerto de Flask
EXPOSE 8080

# 🔟 Ejecutar el script de inicio
CMD ["/app/start.sh"]
