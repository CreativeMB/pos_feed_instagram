#!/bin/sh
# Ejecutar cron en primer plano y enviar todo a stdout para ver logs
supercronic /app/crontab >> /proc/1/fd/1 2>&1 &

# Ejecutar Flask en primer plano
exec python app.py
