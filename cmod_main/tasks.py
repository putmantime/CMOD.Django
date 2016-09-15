from __future__ import absolute_import
from celery.task import periodic_task
from celery.schedules import crontab
from cmod_main.scripts.utils import go_term_resource


@periodic_task(run_every=crontab(hour=14, minute=15), ignore_result=True)
def go_term_update():
    ex = go_term_resource.UpdatePSQLDatabase()
    update = ex.get_go_terms()
    return "updated go terms"

