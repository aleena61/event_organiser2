# Generated by Django 5.1.3 on 2024-11-17 19:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='old_photos',
        ),
        migrations.RemoveField(
            model_name='event',
            name='photos',
        ),
        migrations.CreateModel(
            name='EventPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='events/photos/')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='events.event')),
            ],
        ),
        migrations.CreateModel(
            name='OldPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='events/old_photos/')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='old_photos', to='events.event')),
            ],
        ),
    ]
