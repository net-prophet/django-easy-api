# Generated by Django 2.0 on 2018-08-04 01:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('widgets', '0002_privatewidgetapi_publicwidgetapi'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PrivateWidgetAPI',
        ),
        migrations.DeleteModel(
            name='PublicWidgetAPI',
        ),
    ]
