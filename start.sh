#!/bin/sh
# Ejecutar Flask en segundo plano
python app.py &

# Ejecutar Supercronic en primer plano (logs visibles en Fly)
exec /usr/local/bin/supercronic /app/crontab
