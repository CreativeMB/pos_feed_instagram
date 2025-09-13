from main_app import tarea_programada_publicar_instagram
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

scheduler = BlockingScheduler()

scheduler.add_job(
    tarea_programada_publicar_instagram,
    trigger=CronTrigger(hour=13, minute=55, timezone=pytz.timezone("America/Bogota")),
    id='instagram_daily_post',
    replace_existing=True
)

scheduler.start()
