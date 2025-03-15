from django.db import models
from django.conf import settings  # Импортируем настройки Django


class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.CASCADE)  # Используем кастомную модель пользователя

    # Новые поля для карты
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.title


class EventRegistration(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')  # Один пользователь может записаться только один раз

    def __str__(self):
        return f"{self.user.username} → {self.event.title}"


class EventStage(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='stages')
    title = models.CharField(max_length=255, verbose_name="Название этапа")
    description = models.TextField(blank=True, verbose_name="Описание")
    start_time = models.DateTimeField(verbose_name="Начало этапа")
    end_time = models.DateTimeField(verbose_name="Конец этапа")

    class Meta:
        ordering = ['start_time']
        verbose_name = "Этап мероприятия"
        verbose_name_plural = "Этапы мероприятия"

    def __str__(self):
        return f"{self.event.title} - {self.title}"
