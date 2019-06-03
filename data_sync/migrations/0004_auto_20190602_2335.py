# Generated by Django 2.2 on 2019-06-02 23:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_sync', '0003_datapull_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datapull',
            name='status',
            field=models.CharField(choices=[('SUCCEED', 'SUCCEED'), ('IN_PROGRESS', 'IN_PROGRESS'), ('FAILED', 'FAILED')], default='SUCCEED', help_text='status can become stuck/stale at IN_PROGRESS, if you wait long enough but the status does not change from IN_PROGRESS, please do another sync', max_length=20),
        ),
    ]