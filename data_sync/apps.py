import logging
import os

from django.apps import AppConfig


logger = logging.getLogger('django.data_sync')


class DataSyncConfig(AppConfig):
    name = 'data_sync'
    verbose_name = 'Data sync'

    def ready(self):
        from django.conf import settings

        settings = settings._wrapped.__dict__

        # set to True if you want to force use sync instead
        # this can be useful if you don't want to set up Cloud Tasks
        # and your project is simple enough that you don't need long running
        # tasks
        settings.setdefault('DATA_SYNC_FORCE_SYNC', False)

        settings.setdefault('DATA_SYNC_CLOUD_TASKS_QUEUE_ID', 'data-sync')
        settings.setdefault('DATA_SYNC_CLOUD_TASKS_LOCATION', 'europe-west1')

        settings.setdefault('DATA_SYNC_GOOGLE_CLOUD_PROJECT', os.getenv('GOOGLE_CLOUD_PROJECT', ''))  # noqa
        settings.setdefault('DATA_SYNC_GAE_VERSION', os.getenv('GAE_VERSION', ''))  # noqa
        settings.setdefault('DATA_SYNC_GAE_SERVICE', os.getenv('GAE_SERVICE')),

        settings.setdefault('DATA_SYNC_SERVICE_ACCOUNT_EMAIL', os.getenv('DATA_SYNC_SERVICE_ACCOUNT_EMAIL', ''))  # noqa
