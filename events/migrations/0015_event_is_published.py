# Generated by Django 5.1.7 on 2025-05-26 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0014_event_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='is_published',
            field=models.BooleanField(default=False, verbose_name='Опубликовано'),
        ),
    ]
