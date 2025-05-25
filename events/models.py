from django.db import models
from django.conf import settings
from django.utils import timezone
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
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Стоимость участия (₽)")

    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    image = models.ImageField(upload_to="events/", blank=True, null=True)
    max_participants = models.PositiveIntegerField(default=100)

    registration_closed = models.BooleanField(default=False)

    enable_tasks = models.BooleanField(
        default=True,
        verbose_name="Включить конкурсы и бонусные задания"
    )

    def save(self, *args, **kwargs):
        """Удаляем старый баннер при загрузке нового"""
        if self.pk:
            try:
                old_instance = Event.objects.get(id=self.id)
                if old_instance.image and old_instance.image != self.image:
                    if os.path.isfile(old_instance.image.path):
                        os.remove(old_instance.image.path)
            except Event.DoesNotExist:
                pass

        super().save(*args, **kwargs)

    def is_full(self):
        """Проверяем, заполнено ли мероприятие"""
        return self.eventregistration_set.count() >= self.max_participants

    def check_and_close_registration(self):
        """Закрывает регистрацию, если мероприятие уже началось"""
        now = timezone.now()
        if not self.registration_closed and now >= self.start_time:
            self.registration_closed = True
            self.save(update_fields=['registration_closed'])

    @classmethod
    def close_expired_registrations(cls):
        """Закрывает регистрацию для всех мероприятий, у которых уже началось событие"""
        now = timezone.now()
        events_to_close = cls.objects.filter(start_time__lte=now, registration_closed=False)
        for event in events_to_close:
            event.registration_closed = True
            event.save(update_fields=['registration_closed'])

    def is_registration_open(self):
        """Определяет, можно ли записываться"""
        return not self.registration_closed and not self.is_full()

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

    def remove_registration(self, requester):
        """Удаляет участника с мероприятия (только для организатора или админа)"""
        if requester == self.event.organizer or requester.is_superuser:
            self.delete()
            return True
        return False


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


class EventTask(models.Model):
    TYPE_CODE = 'code'
    TYPE_QUESTION = 'question'

    TASK_TYPES = [
        (TYPE_CODE, 'Кодовое слово / QR-код'),
        (TYPE_QUESTION, 'Ответ на вопрос'),
    ]

    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TASK_TYPES, default=TYPE_CODE)
    code = models.CharField(max_length=100, help_text="Код или правильный ответ", blank=True, null=True)
    reward = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Задание"
        verbose_name_plural = "Задания"

    def __str__(self):
        return f"{self.title} ({self.get_type_display()})"


class TaskCompletion(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey(EventTask, on_delete=models.CASCADE)
    submitted_answer = models.CharField(max_length=255, blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'task')
        verbose_name = "Выполнение задания"
        verbose_name_plural = "Выполненные задания"

    def __str__(self):
        return f"{self.user.username} → {self.task.title}"


class BonusTask(models.Model):
    CODE = 'code'
    SYSTEM = 'system'

    TASK_TYPES = [
        (SYSTEM, 'Системное задание'),
        (CODE, 'Бонус-код'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    reward = models.PositiveIntegerField()  # Баллы
    type = models.CharField(max_length=20, choices=TASK_TYPES, default=SYSTEM)
    code = models.CharField(max_length=50, blank=True, null=True, unique=True)
    is_active = models.BooleanField(default=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="bonus_tasks", null=True, blank=True)
    admin_only = models.BooleanField(default=False, verbose_name="Только для админов")

    def __str__(self):
        return f"{self.name} ({self.reward} баллов)"


class BonusTaskCompletion(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey(BonusTask, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'task')  # нельзя выполнить дважды

    def __str__(self):
        return f"{self.user.username} — {self.task.name}"
