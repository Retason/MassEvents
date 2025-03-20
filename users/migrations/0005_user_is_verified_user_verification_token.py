# Generated by Django 5.1.7 on 2025-03-20 15:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_user_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='verification_token',
            field=models.UUIDField(blank=True, editable=False, null=True, unique=True),
        ),
    ]
