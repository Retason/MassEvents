from django.db import models
from django.conf import settings
import os


def event_image_upload_path(instance, filename):
    """Генерирует путь для сохранения изображений мероприятий"""
    return f'events/{instance.id}/{filename}'


class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    image = models.ImageField(upload_to=event_image_upload_path, blank=True, null=True)
    max_participants = models.PositiveIntegerField(default=100)

    def save(self, *args, **kwargs):
        """Удаляем старый баннер при загрузке нового"""
        try:
            old_instance = Event.objects.get(id=self.id)
            if old_instance.image and old_instance.image != self.image:
                if os.path.isfile(old_instance.image.path):
                    os.remove(old_instance.image.path)
        except Event.DoesNotExist:
            pass  # Если объект новый, пропускаем проверку

        super().save(*args, **kwargs)

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
