# Generated by Django 5.1.7 on 2025-05-15 04:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0012_bonustaskcompletion'),
    ]

    operations = [
        migrations.AddField(
            model_name='bonustask',
            name='admin_only',
            field=models.BooleanField(default=False, verbose_name='Только для админов'),
        ),
    ]
