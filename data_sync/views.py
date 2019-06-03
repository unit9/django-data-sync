import json
import logging

from django.conf import settings
from django.core.validators import URLValidator
from django.http import JsonResponse
from django.views import View

import data_sync
from data_sync import models

url_validator = URLValidator()


logger = logging.getLogger('django.data_sync')


class DataSyncExportAPIView(View):
    """Export insensitive data that are meant to be synced between env"""

    def get(self, request):
        data = data_sync.export()
        return JsonResponse(data, safe=False)


class DataSyncExportFilesConfigurationView(View):
    """
    Export insensitive settings.

    Built to help target env to have correct base media URl to download
    the files.
    """

    # nice to have, move the logic to data_sync module
    def get(self, request):
        if settings.DEFAULT_FILE_STORAGE == 'storages.backends.gcloud.GoogleCloudStorage':  # noqa
            # this string is hardcoded in google cloud storage library anyway
            base_url = 'https://storage.googleapis.com/{}'.format(settings.GS_BUCKET_NAME)  # noqa
        else:
            raise NotImplementedError
        data = {
            'media_base_url': base_url
        }
        return JsonResponse(data)


class RunDataSyncGAECloudTasks(View):
    def post(self, request):
        logger.debug(
            f'Incoming data pull Cloud Tasks request. Data {request.body.decode()}'  # noqa
        )
        errors = {}
        try:
            data = json.loads(request.body.decode())
        except Exception:
            errors = {'errors': ['could not parse JSON']}

        if not all(key in data for key in ('token', 'data_pull_id', 'data_source_base_url')):  # noqa
            errors = {'errors': ['token, data_pull_id, data_source_base_url are needed']}  # noqa

        try:
            data_pull = models.DataPull.objects.get(id=data['data_pull_id'])
        except Exception:
            errors = {'errors': ['Invalid data_pull_id']}

        if errors:
            logger.warning(errors)
            return JsonResponse(data=errors, status=400)

        try:
            url_validator(data['data_source_base_url'])
        except Exception:
            data_pull.status = 'FAILED'
            data_pull.save()

            errors = {'errors': ['data_source_base_url is not a valid URL']}
            logger.warning(errors)
            return JsonResponse(
                data=errors, status=400
            )
        try:
            data_sync.run(data['data_source_base_url'])
        except Exception:
            data_pull.status = 'FAILED'
        else:
            data_pull.status = 'SUCCEED'
        data_pull.save()

        return JsonResponse(data={'status': 'created'}, status=201)
