#!/bin/bash
echo ">>> Iniciando aplicación con Supercronic + Flask (zona horaria: $TZ)"

# Lanzar Flask en segundo plano
python app.py &
FLASK_PID=$!

# Esperar unos segundos
sleep 5

# Lanzar supercronic
exec /usr/local/bin/supercronic /app/crontab
