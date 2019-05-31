import os

from django.apps import AppConfig


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

        settings.setdefault('DATA_SYNC_GAE_APPLICATION', os.getenv('GAE_APPLICATION', ''))  # noqa
        settings.setdefault('DATA_SYNC_GAE_VERSIONM', os.getenv('GAE_VERSIION', ''))  # noqa

        if settings['DEBUG']:
            token = os.getenv('DATA_SYNC_TOKEN', '')
        else:
            # mandatory if non debug to fill the token
            token = os.getenv('DATA_SYNC_TOKEN')
        settings.setdefault('DATA_SYNC_TOKEN', token)
