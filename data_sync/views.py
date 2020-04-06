import copy
import json
import logging
import traceback

import oidc_validators
from django.conf import settings
from django.core.validators import URLValidator
from django.http import JsonResponse
from django.views import View

import data_sync
from data_sync import models
from data_sync.gcp.task_queues import get_cloud_task_handler_url

url_validator = URLValidator()


logger = logging.getLogger('django.data_sync')


class AuthTokenProtectedMixin:

    def dispatch(self, request, *args, **kwargs):
        if settings.DATA_SYNC_EXPORT_TOKEN:
            auth = request.headers.get('Authorization', '')
            try:
                auth, token = auth.split(' ')
            except ValueError:
                return JsonResponse(data={}, status=401)
            if token != settings.DATA_SYNC_EXPORT_TOKEN:
                return JsonResponse(data={}, status=401)
        return super().dispatch(request, *args, **kwargs)


class DataSyncExportAPIView(AuthTokenProtectedMixin, View):
    """Export insensitive data that are meant to be synced between env"""

    def get(self, request, *args, **kwargs):
        data = data_sync.export()
        return JsonResponse(data, safe=False)


class DataSyncExportFilesConfigurationView(AuthTokenProtectedMixin, View):
    """
    Export insensitive settings.

    Built to help target env to have correct base media URl to download
    the files.
    """

    # TODO nice to have, move the logic to data_sync module
    def get(self, request, *args, **kwargs):
        if settings.DATA_SYNC_MEDIA_FILES_BASE_URL:
            media_base_url = settings.DATA_SYNC_MEDIA_FILES_BASE_URL
        elif settings.DEFAULT_FILE_STORAGE == 'storages.backends.gcloud.GoogleCloudStorage':  # noqa
            # if you separate env per bucket this could work,
            # if you have prefix then you must specify the above
            media_base_url = 'https://storage.googleapis.com/{}'.format(settings.GS_BUCKET_NAME)  # noqa
        else:
            # TODO make this string constant
            media_base_url = 'no_files_sync'
        data = {'media_base_url': media_base_url}
        return JsonResponse(data)


class RunDataSyncGAECloudTasks(View):
    def post(self, request):
        errors = {}
        try:
            data = json.loads(request.body.decode())
        except Exception:
            errors = {'errors': ['could not parse JSON']}
            return JsonResponse(data=errors, status=400)

        debugging_data = copy.deepcopy(data)
        logger.debug(
            f'Incoming data pull Cloud Tasks request. Data {debugging_data} Headers: {request.headers}'  # noqa
        )

        if not all(key in data for key in ('data_pull_id', 'data_source_base_url')):  # noqa
            errors = {'errors': ['data_pull_id, data_source_base_url are needed']}  # noqa

        data_pull = None
        try:
            data_pull = models.DataPull.objects.get(id=data['data_pull_id'])
        except Exception:
            errors = {'errors': ['Invalid data_pull_id']}

        if errors:
            logger.warning(errors)
            if data_pull:
                data_pull.status = 'FAILED'
                data_pull.save()
            return JsonResponse(data=errors, status=400)

        assert data_pull

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

        oidc_token = request.headers.get('Authorization', '')
        if not oidc_token:
            errors = {'errors': 'Authorization not present in headers, malicious request!'}  # noqa
            logger.warning(errors)
            return JsonResponse(data=errors, status=401)

        oidc_token = oidc_token.split(' ')[1]  # strip Bearer

        try:
            oidc_validators.Google.validate(
                token=oidc_token,
                email=settings.DATA_SYNC_SERVICE_ACCOUNT_EMAIL,
                audience=get_cloud_task_handler_url(
                    data['data_source_base_url']
                )
            )
        except Exception as e:
            traceback.format_exc()
            logger.error(e, exc_info=True)
            errors = {'errors': 'Failed to validate OIDC'}
            return JsonResponse(data=errors, status=400)

        try:
            data_sync.run(data['data_source_base_url'])
        except Exception as e:
            traceback.format_exc()
            logger.error(e, exc_info=True)
            data_pull.status = 'FAILED'
        else:
            data_pull.status = 'SUCCEED'

        data_pull.save()

        return JsonResponse(data={'status': 'created'}, status=201)
