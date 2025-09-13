# scheduler.py
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from main_app import tarea_programada_publicar_instagram  # Importa la función desde app principal
import pytz

def iniciar_scheduler():
    scheduler = BlockingScheduler()
    

    scheduler.add_job(
        tarea_programada_publicar_instagram,
        trigger=CronTrigger(hour=12, minute=45, timezone=pytz.timezone("America/Bogota")),
        id='instagram_daily_post',
        replace_existing=True
    )
    
    print("Scheduler iniciado. Publicación diaria programada a las 12:35 PM hora Bogotá.")
    scheduler.start()


if __name__ == "__main__":
    iniciar_scheduler()
