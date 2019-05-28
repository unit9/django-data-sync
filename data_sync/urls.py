from django.urls import path

from . import views

namespace = 'data_sync'

urlpatterns = [
    path('export', views.DataSyncExportAPIView.as_view(), name='export'),
    path('export/files/configuration', views.DataSyncExportFilesConfigurationView.as_view(), name='export_files_configuration')  # noqa
]
