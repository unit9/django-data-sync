# Generated by Django 2.2 on 2019-05-31 07:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_sync', '0002_auto_20190528_0217'),
    ]

    operations = [
        migrations.AddField(
            model_name='datapull',
            name='status',
            field=models.CharField(choices=[('SUCCEED', 'SUCCEED'), ('IN_PROGRESS', 'IN_PROGRESS'), ('FAILED', 'FAILED')], default='SUCCEED', max_length=20),
        ),
    ]
