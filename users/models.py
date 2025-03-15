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

    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser

    def is_organizer(self):
        return self.role == self.ORGANIZER or self.is_admin()
