FROM python:3.11-slim

# Instalar dependencias de Chromium
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libx11-xcb1 \
    libxcb1 \
    libxkbcommon0 \
    libexpat1 \
    libdbus-1-3 \
    libatspi2.0-0 \
    wget curl gnupg ca-certificates fonts-liberation \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

ENV PORT=8080
CMD ["python3", "app.py"]


