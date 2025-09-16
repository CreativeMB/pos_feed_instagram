#!/bin/sh
# Ejecutar Flask en segundo plano
python app.py &

# Ejecutar Supercronic en primer plano (logs aparecerán en fly logs)
exec supercronic /app/crontab
