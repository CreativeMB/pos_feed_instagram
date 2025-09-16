#!/bin/bash
echo ">>> Iniciando aplicación con Supercronic + Flask (zona horaria: $TZ)"

# Lanzar Flask en segundo plano
python app.py &
FLASK_PID=$!

# Esperar hasta que Flask realmente esté respondiendo
echo ">>> Esperando a que Flask levante..."
until curl -s http://localhost:8080/ >/dev/null 2>&1; do
    sleep 2
done
echo ">>> Flask está listo."

# 🔥 Disparar inicialización automática
echo ">>> Ejecutando inicialización automática..."
curl -s http://localhost:8080/publicar_ahora || true

# Lanzar supercronic en primer plano (cron jobs)
exec /usr/local/bin/supercronic /app/crontab
