from django.contrib import admin

from data_sync import models


class TimeStampedModelAdminMixin:
    def get_exclude(self, request, obj=None):
        super_fields = super().get_exclude(request, obj)
        if super_fields:
            return tuple(super_fields) + ('time_created', 'time_updated')
        else:
            return 'time_created', 'time_updated'


@admin.register(models.DataSource)
class DataSourceAdmin(TimeStampedModelAdminMixin, admin.ModelAdmin):
    pass


@admin.register(models.DataPull)
class DataPullAdmin(TimeStampedModelAdminMixin, admin.ModelAdmin):
    actions = None
    list_per_page = 20
    list_display = (
        'time_created',
        'data_source',
        'status'
    )

    def get_queryset(self, request):
        return models.DataPull.objects.all().select_related('data_source')

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return 'data_source', 'status'
        else:
            return 'status',
