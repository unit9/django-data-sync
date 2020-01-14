import logging

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

import data_sync
from data_sync import GrabExportError, gcp
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
        default='',
        max_length=20,
        choices=(
            ('', ''),
            ('SUCCEED', 'SUCCEED'),
            ('IN_PROGRESS', 'IN_PROGRESS'),
            ('FAILED', 'FAILED')
        ),
        blank=True,
        help_text='status can become stuck/stale at IN_PROGRESS, if you wait '
                  'long enough but the status does not change from IN_PROGRESS'
                  ', please do another sync'
    )

    def save(self, *args, **kwargs):
        self.status = 'IN_PROGRESS' if not self.status else self.status
        super().save(*args, **kwargs)

        if self.status == 'IN_PROGRESS':
            if runtime_utils.is_in_gae():
                gcp.task_queues.create_run_data_sync_task(
                    data_pull_id=self.id,
                    data_source_base_url=self.data_source.env_url
                )
            else:
                try:
                    data_sync.run(self.data_source.env_url)
                except GrabExportError as e:
                    raise ValidationError(
                        'Failed to get data from source. Most likely you have '
                        'invalid Data Source URL. Please refer to docs'
                    )
                self.status = 'SUCCEED'
                self.save()

    def __str__(self):
        return 'Sync from {} at {}'.format(
            self.data_source,
            self.time_created
        )
