#!/bin/bash
echo ">>> Iniciando aplicación con Supercronic + Flask (zona horaria: $TZ)"

# Lanzar publicación inicial en background usando Python directamente
echo ">>> Ejecutando publicación inicial con Python..."
python -c "from app import tarea_programada_publicar_instagram; tarea_programada_publicar_instagram()" || true

# Lanzar Flask en segundo plano
python app.py &
FLASK_PID=$!

# Esperar unos segundos a que Flask levante
sleep 5

# Lanzar supercronic en primer plano (cron jobs)
exec /usr/local/bin/supercronic /app/crontab
