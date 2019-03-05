from django.http import JsonResponse
from django.views import View

import data_sync


class DataSyncExportAPIView(View):
    """Export insensitive data that are meant to be synced between env"""

    def get(self, request):
        data = data_sync.export()
        return JsonResponse(data, safe=False)
