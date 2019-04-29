from base64 import b64decode
from collections import defaultdict
from io import BytesIO

from django.apps import apps
from django.core import serializers
from django.core.files import File

import data_sync.managers
from data_sync.exceptions import GrabExportError
from data_sync.registration import register_model

import requests


default_app_config = 'data_sync.apps.DataSyncConfig'


"""
Changing natural key means the object will be deleted.
This won't be a problem however since the objects will be created
all along with all its relations with new natural key(s)

Keep in mind that Django Deserialization have the ability to edit
existing objects, which is not available in loaddata command.
That's why there's no logic to handle changed objects
"""


def pull(data_source_url):
    """
    In a sync, you want to sync both what's in the DB and the media files
    that's why it's coupled
    :param data_source_url: env_url from DataSource
    :return: tuple of exported data
    """
    url = data_source_url + '/export'
    try:
        # will convert to python list of serialized objects strings
        data = requests.get(url).json()
    except Exception as e:
        raise GrabExportError()
    return data


def export():
    """
    This will return a list, which each element is serialized objects
    (per model) using Django built in serializer
    """
    data = []
    for Model in data_sync.registration.sort_dependencies():
        objects = Model.objects.all()
        if not objects:
            continue

        serialized_objects = serializers.serialize(
            'json',
            objects,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
            fields=Model._data_sync_fields
        )
        data.append(serialized_objects)
    return data


def django_sync(pulled_data):
    """
    They heavy lifting, thanks to Django magic.
    Since we need to also delete things, when locale is given, do not
    delete translations in other locales.
    """
    processed_ids = defaultdict(list)

    for serialized_objects_per_model in pulled_data:
        for obj in serializers.deserialize('json', serialized_objects_per_model):  # noqa
            obj.save()
            processed_ids[obj.object.__class__].append(obj.object.id)

    for Model, ids in processed_ids.items():
        Model.objects.exclude(id__in=ids).delete()


def run(data_source_base_url, is_generate_compare_data=False):
    """
    Run the data sync process, returns compare data to be saved to DataPull
    for audit/history purposes
    """
    pulled_data = pull(data_source_base_url)

    if is_generate_compare_data:
        raise NotImplementedError
    else:
        django_sync(pulled_data)
        compare_data = None

    return compare_data
