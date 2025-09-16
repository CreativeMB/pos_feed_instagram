#!/bin/bash
set -e

# Iniciar cron en segundo plano
cron

# Mostrar logs de cron en la salida estándar
tail -f /var/log/cron.log &

# Iniciar Flask en primer plano
exec python app.py
