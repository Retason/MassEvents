import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ADMIN = 'admin'
    ORGANIZER = 'organizer'
    PARTICIPANT = 'participant'

    ROLE_CHOICES = [
        (ADMIN, 'Администратор'),
        (ORGANIZER, 'Организатор'),
        (PARTICIPANT, 'Обычный пользователь')
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=PARTICIPANT)
    is_verified = models.BooleanField(default=False)  # Флаг подтверждения email

    # Теперь поле может быть пустым при миграции, но заполнится при создании пользователя
    verification_token = models.UUIDField(unique=True, editable=False, null=True, blank=True)

    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser

    def is_organizer(self):
        return self.role == self.ORGANIZER or self.is_admin()

    def generate_verification_token(self):
        """Создаёт новый токен подтверждения email"""
        self.verification_token = uuid.uuid4()
        self.save(update_fields=['verification_token'])

    def save(self, *args, **kwargs):
        """Генерируем токен, если его нет"""
        if not self.verification_token:
            self.verification_token = uuid.uuid4()
        super().save(*args, **kwargs)
