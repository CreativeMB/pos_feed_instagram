# scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from main_app import tarea_programada_publicar_instagram
import pytz
import time


scheduler = BlockingScheduler()

# Programación diaria a las 12:10 PM hora Bogotá
scheduler.add_job(
    tarea_programada_publicar_instagram,
    trigger=CronTrigger(hour=12, minute=35, timezone=pytz.timezone("America/Bogota")),
    id='instagram_daily_post',
    name='Publicación diaria a las 12:10 PM (hora Colombia)',
    replace_existing=True
)

print("Scheduler iniciado. La publicación diaria está programada a las 12:10 PM hora Colombia.")
scheduler.start()
