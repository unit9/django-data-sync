from django.urls import path

from . import views

namespace = 'data_sync'

urlpatterns = [
    path('export', views.DataSyncExportAPIView.as_view(), name='export')
]
