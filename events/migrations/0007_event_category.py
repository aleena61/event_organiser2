# Generated by Django 5.1.3 on 2024-12-15 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0006_event_newsletter_event_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='category',
            field=models.CharField(choices=[('cultural', 'Cultural'), ('sports', 'Sports'), ('music', 'Music'), ('tech', 'Tech'), ('art', 'Art')], default='cultural', max_length=20),
        ),
    ]
