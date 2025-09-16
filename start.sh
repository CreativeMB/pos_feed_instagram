#!/bin/bash
echo ">>> Iniciando aplicación con Supercronic + Flask (zona horaria: $TZ)"

# Lanzar Flask en segundo plano
python app.py &

# Esperar unos segundos a que Flask levante
sleep 10

# 🔥 Disparar inicialización automática (como si fuera la primera visita)
curl -s http://localhost:8080/publicar_ahora || true

# Lanzar supercronic en primer plano (se queda corriendo)
exec /usr/local/bin/supercronic /app/crontab
