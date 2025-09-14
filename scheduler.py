from app import tarea_programada_publicar_instagram
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

scheduler = BlockingScheduler()

# Job programado diario para las 6:00 PM (Hora de Bogotá)
scheduler.add_job(
    tarea_programada_publicar_instagram,
    trigger=CronTrigger(hour=19, minute=30, timezone=pytz.timezone("America/Bogota")),
    id='instagram_daily_post',
    replace_existing=True
)

# Job que se ejecuta inmediatamente al arrancar (mantenerlo para el primer inicio)
scheduler.add_job(
    tarea_programada_publicar_instagram,
    trigger='date',  # Se ejecuta solo una vez
    id='instagram_immediate_post',
    replace_existing=True
)

print("Scheduler iniciado. Publicación diaria programada (6:00 PM Bogotá) y disparo inmediato en curso.")
scheduler.start()
