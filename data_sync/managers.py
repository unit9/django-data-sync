from django.db import models


class DataSyncEnhancedManager(models.Manager):
    def get_by_natural_key(self, *args, **kwargs):
        _kwargs = {
            _natural_key.replace('.', '__'): arg
            for _natural_key, arg
            in zip(self.model._data_sync_natural_key, args)
        }
        return self.get(**_kwargs)
