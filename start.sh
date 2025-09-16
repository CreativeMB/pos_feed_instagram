#!/bin/bash
echo ">>> Iniciando aplicación con Supercronic + Flask (zona horaria: $TZ)"

# Lanzar Flask en segundo plano
python app.py &
FLASK_PID=$!

# Esperar hasta que Flask y la ruta /publicar_ahora estén disponibles
echo ">>> Esperando a que Flask levante..."
for i in {1..20}; do
    if curl -s http://localhost:8080/publicar_ahora >/dev/null 2>&1; then
        echo ">>> Flask está listo y /publicar_ahora responde"
        break
    else
        echo ">>> Intento $i: aún no responde, reintentando..."
        sleep 3
    fi
done

# 🔥 Publicación inicial para confirmar despliegue
echo ">>> Ejecutando publicación inicial tras el despliegue..."
RESPUESTA=$(curl -s http://localhost:8080/publicar_ahora || echo "Error en publicación inicial")
echo ">>> Respuesta inicial: $RESPUESTA"

# Lanzar supercronic en primer plano (cron jobs)
exec /usr/local/bin/supercronic /app/crontab

