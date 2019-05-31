import json
import logging
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from google.cloud import tasks_v2

import data_sync
from data_sync import GrabExportError
from data_sync import runtime_utils


logger = logging.getLogger('django.data_sync')


class TimeStampedModel(models.Model):
    time_created = models.DateTimeField(blank=True, null=True,
                                        verbose_name='Created')
    time_updated = models.DateTimeField(blank=True, null=True,
                                        verbose_name='Updated')

    def save(self, *args, **kwargs):
        now = timezone.now()
        if not self.time_created:
            self.time_created = now

        self.time_updated = now
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class DataSource(TimeStampedModel):
    env_name = models.CharField(
        max_length=20,
        help_text='Identifier of the source env e.g. develop',
        unique=True
    )
    env_url = models.URLField(
        verbose_name='environment base URL',
        help_text=(
            'Environment base URL where the data will be pulled from. '
            'Scheme included and do not include endslash.'
            'This value is very dependant on the urls.py setup, refers to '
            'django_data_sync docs for further explanation.'
            "Usually it's https://example.com/api"
        )
    )

    def __str__(self):
        return '{} - {}'.format(self.env_name, self.env_url)


class DataPull(TimeStampedModel):
    data_source = models.ForeignKey(DataSource, related_name='data_pulls',
                                    null=True, on_delete=models.SET_NULL)

    compare_data = models.TextField(blank=True, null=True)

    status = models.CharField(
        default='SUCCEED',
        max_length=20,
        choices=(
            ('SUCCEED', 'SUCCEED'),
            ('IN_PROGRESS', 'IN_PROGRESS'),
            ('FAILED', 'FAILED')
        ),
        help_text='status can become stuck/stale at IN_PROGRESS, if you wait '
                  'long enough but the status does not change from IN_PROGRESS'
                  ', please do another sync'
    )

    @staticmethod
    def _create_run_data_sync_task(data_pull_id, data_source_base_url):
        """
        Calls self version to run data sync
        """
        client = tasks_v2.CloudTasksClient()

        parent = client.queue_path(
            settings.DATA_SYNC_GAE_APPLICATION,
            settings.DATA_SYNC_CLOUD_TASKS_LOCATION,
            settings.DATA_SYNC_CLOUD_TASKS_QUEUE_ID
        )

        url = f'https://{settings.DATA_SYNC_GAE_VERSION}-dot-{settings.DATA_SYNC_GAE_APPLICATION}'  # noqa

        # since data sync urls can be registered inside another naemspace
        # we can't reverse it reliably
        # however, we can infer it from the data_source_base_url
        parsed_data_source_base_url = urlparse(data_source_base_url)

        project_dependent_namespace = parsed_data_source_base_url.path

        url += project_dependent_namespace

        # TODO make this as a constant

        url += '/data_sync/run/gae/cloudtasks'

        data = {
            # use custom token temporarily :))))
            # GCP recommends OIDC
            'token': settings.DATA_SYNC_TOKEN.encode(),
            'data_pull_id': data_pull_id,
            'data_source_base_url': data_source_base_url
        }
        encoded_data = json.dumps(data).encode()

        task = {
            'http_request': {
                'http_method': 'POST',
                'url': url,
                'body': encoded_data
            },
        }

        response = client.create_task(parent, task)

        logger.info(
            f'Data pull task initiated. ID: {data_pull_id} '
            f'SOURCE_URL: {data_source_base_url}'
        )

        return response

    def save(self, *args, **kwargs):
        self.status = 'IN_PROGRESS'
        super().save(*args, **kwargs)

        if runtime_utils.is_in_gae():
            self._create_run_data_sync_task(self.id, self.data_source.env_url)

        try:
            data_sync.run(self.data_source.env_url)
        except GrabExportError as e:
            raise ValidationError(
                'Failed to get data from source. Most likely you have '
                'invalid Data Source URL. Please refer to docs'
            )

    def __str__(self):
        return 'Sync from {} at {}'.format(
            self.data_source,
            self.time_created
        )
