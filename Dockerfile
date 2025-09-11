FROM python:3.11-bullseye

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
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
    wget \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

