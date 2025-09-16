#!/bin/bash
set -e

echo ">>> Iniciando aplicación con Supercronic + Flask (zona horaria: $TZ)"

# Lanzar Flask en segundo plano
python app.py &

# Lanzar supercronic con el archivo crontab (en primer plano para que Fly capture logs)
exec /usr/local/bin/supercronic /app/crontab
