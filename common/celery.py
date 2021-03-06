from __future__ import absolute_import

import os

from celery import Celery, states
from celery.exceptions import Ignore

from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cmod.settings')
# os.environ.setdefault('DJANGO_CONFIGURATION', 'Production')

app = Celery('cmod')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    logger.debug('Debug Task', exc_info=True, extra={'self': self})


@app.task(bind=True)
def warning_task(self, msg):
    if not self.request.called_directly:
        self.update_state(state=states.SUCCESS, meta=msg)
        raise Ignore()
