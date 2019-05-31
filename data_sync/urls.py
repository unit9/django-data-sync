from django.urls import path

from . import views

app_name = 'data_sync'

urlpatterns = [
    path('data_sync/export', views.DataSyncExportAPIView.as_view(), name='export'),
    path('data_sync/export/files/configuration', views.DataSyncExportFilesConfigurationView.as_view(), name='export_files_configuration'),  # noqa
    path('data_sync/run/gae/cloudtasks', views.RunDataSyncGAECloudTasks.as_view(), name='run_gae_cloudtasks')  # noqa
]
