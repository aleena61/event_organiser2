# Generated by Django 5.1.3 on 2025-01-05 09:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0015_event_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
