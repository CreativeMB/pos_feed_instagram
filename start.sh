#!/bin/sh
# Ejecutar supercronic en segundo plano
supercronic /app/crontab &
# Ejecutar Flask en primer plano
exec python app.py
