from django.conf import settings
from django.http import JsonResponse
from django.views import View

import data_sync


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
