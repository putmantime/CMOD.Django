from __future__ import absolute_import
from celery.task import periodic_task
from celery.schedules import crontab
from cmod_main.scripts.utils import go_term_resource, prepare_ref_seq_configs


@periodic_task(run_every=crontab(hour=0, minute=0), ignore_result=True)
def go_term_update():
    ex = go_term_resource.UpdatePSQLDatabase()
    update = ex.get_go_terms()
    return "updated go terms"

@periodic_task(run_every=crontab(hour=1, minute=0), ignore_result=True)
def reference_sequence_update():
    rsu = prepare_ref_seq_configs.PrepareRefSeqs()
    return "updated reference sequences"