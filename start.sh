#!/bin/bash
echo ">>> Iniciando aplicación con Supercronic + Flask (zona horaria: $TZ)"

# 🔥 Publicación inicial REAL con log
echo ">>> Ejecutando publicación inicial de despliegue..."
python - <<'EOF'
from app import tarea_programada_publicar_instagram
try:
    print(">>> 🚀 Iniciando publicación inicial de despliegue...")
    tarea_programada_publicar_instagram()
    print("✅ Publicación inicial de despliegue ejecutada correctamente.")
except Exception as e:
    print(f"❌ Error en la publicación inicial de despliegue: {e}")
EOF

# Lanzar Flask en segundo plano
python app.py &
FLASK_PID=$!

# Esperar unos segundos a que Flask levante
sleep 5

# Lanzar supercronic en primer plano (cron jobs programados)
exec /usr/local/bin/supercronic /app/crontab
