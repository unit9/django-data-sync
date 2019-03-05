from operator import attrgetter

from django.apps import apps
from django.core.serializers import sort_dependencies as _sort_dependencies

from data_sync.managers import DataSyncEnhancedManager

registered_models = []


def register_model(natural_key, fields=None):
    def _natural_key(self):
        natural_key_values = [
            attrgetter(natural_key)(self)
            for natural_key
            in self._data_sync_natural_key
        ]
        return natural_key_values

    def Model(model):
        model._data_sync_fields = fields
        model._data_sync_natural_key = natural_key
        model.natural_key = _natural_key
        if not isinstance(model.objects, DataSyncEnhancedManager):
            raise ValueError(
                'default manager is not a class or subclass of '
                'DataSyncEnhancedManager'
            )
        registered_models.append(model)
        return model

    return Model


def sort_dependencies():
    configs = apps.get_app_configs()
    app_list = (
        (config, None) for config in configs
    )
    sorted_models = _sort_dependencies(app_list)

    sorted_dependencies = [
        model
        for model
        in sorted_models
        if model in registered_models
    ]

    return sorted_dependencies
