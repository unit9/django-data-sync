from collections import defaultdict
from io import BytesIO

from django.conf import settings
from django.core import serializers
from django.core.files import File

import requests

import data_sync.managers
from data_sync.exceptions import GrabExportError
from data_sync.registration import register_model
from data_sync import url_constants


default_app_config = 'data_sync.apps.DataSyncConfig'


"""
Changing natural key means the object will be deleted.
This won't be a problem however since the objects will be created
all along with all its relations with new natural key(s)

Keep in mind that Django Deserialization have the ability to edit
existing objects, which is not available in loaddata command.
That's why there's no logic to handle changed objects
"""


def get_export_request_headers():
    # TODO find how lazy settings works so this can be moved to module level
    return {
        'Authorization': f'Token {settings.DATA_SYNC_EXPORT_TOKEN}'
    } if settings.DATA_SYNC_EXPORT_TOKEN else None


def pull_data(data_source_url):
    """
    :param data_source_url: env_url from DataSource
    :return: tuple of exported data
    """
    url = f'{data_source_url}/{url_constants.EXPORT}'

    try:
        # will convert to python list of serialized objects strings
        data = requests.get(
            url,
            headers=get_export_request_headers(),
            timeout=10
        ).json()
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
            fields=Model._data_sync_fields + Model._data_sync_file_fields
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

    registered_models = data_sync.registration.sort_dependencies()
    for Model, ids in processed_ids.items():
        Model.objects.exclude(id__in=ids).delete()

        # remove processed model, if there's still any
        # then no objects present in that model in the source env
        registered_models.remove(Model)

    if registered_models:
        for Model in registered_models:
            Model.objects.all().delete()


def files_sync(data_source_base_url):
    """
    Download all the files from source env to target env and save it
    """
    media_base_url = requests.get(
        f'{data_source_base_url}/{url_constants.EXPORT_FILES_CONFIGURATION}',
        headers=get_export_request_headers(),
        timeout=10
    ).json()['media_base_url']
    if media_base_url == 'no_files_sync':
        return

    for Model in data_sync.registration.sort_dependencies():
        if not Model._data_sync_file_fields:
            continue

        qs = Model.objects.all().only(Model._data_sync_file_fields)

        for obj in qs.iterator():
            for file_field_name in Model._data_sync_file_fields:
                file_field = getattr(obj, file_field_name, None)
                if file_field is None:
                    continue

                r = requests.get(
                    f'{media_base_url}/{file_field.name}',
                    timeout=10
                )
                if not r.ok:
                    continue

                bytes_content = BytesIO(r.content)

                new_file = File(bytes_content)
                file_field.save(file_field.name, new_file, save=True)
                new_file.close()


def run(data_source_base_url, is_generate_compare_data=False):
    """
    Run the data sync process, returns compare data to be saved to DataPull
    for audit/history purposes
    """
    pulled_data = pull_data(data_source_base_url)

    if is_generate_compare_data:
        raise NotImplementedError
    else:
        django_sync(pulled_data)
        files_sync(data_source_base_url)
        compare_data = None

    return compare_data
