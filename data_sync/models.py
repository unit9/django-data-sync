from django.db import models
from django.utils import timezone


import data_sync


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
        help_text=('Environment base URL where the data will be pulled from. '
                   'Scheme included and do not include endslash')
    )

    def __str__(self):
        return '{} - {}'.format(self.env_name, self.env_url)


class DataPull(TimeStampedModel):
    data_source = models.ForeignKey(DataSource, related_name='data_pulls',
                                    null=True, on_delete=models.SET_NULL)

    compare_data = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        data_sync.run(self.data_source.env_url)

    def __str__(self):
        return 'Sync from {} at {}'.format(
            self.data_source,
            self.time_created
        )
