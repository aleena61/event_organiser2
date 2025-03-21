# Generated by Django 5.1.3 on 2024-12-15 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0008_event_created_at_event_updated_at_alter_event_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='delete_requested',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event',
            name='requested_approval',
            field=models.BooleanField(default=False),
        ),
    ]
