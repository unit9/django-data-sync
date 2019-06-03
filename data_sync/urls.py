from django.urls import path

from data_sync import views
from data_sync import url_constants

app_name = 'data_sync'

urlpatterns = [
    path(url_constants.EXPORT, views.DataSyncExportAPIView.as_view(), name='export'),
    path(url_constants.EXPORT_FILES_CONFIGURATION, views.DataSyncExportFilesConfigurationView.as_view(), name='export_files_configuration'),  # noqa
    path(url_constants.RUN_DATA_SYNC_GAE_CLOUD_TASKS, views.RunDataSyncGAECloudTasks.as_view(), name='run_gae_cloudtasks')  # noqa
]
