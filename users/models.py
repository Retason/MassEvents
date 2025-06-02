import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from events.models import BonusTask


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

    # Баланс пользователя (1 балл = 1 рубль)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Кошелёк (₽)")
    bonus_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Бонусы")

    # Токен подтверждения email
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


class WalletTransaction(models.Model):
    '''Транзакции кошелька (рубли)'''
    INCOME = 'income'
    EXPENSE = 'expense'

    TRANSACTION_TYPES = [
        (INCOME, 'Пополнение'),
        (EXPENSE, 'Списание'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    admin_response = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.type == self.INCOME else '-'
        return f"{sign}{self.amount}₽ - {self.description}"


# История начислений бонусов
class BonusTransaction(models.Model):
    INCOME = 'income'
    EXPENSE = 'expense'
    TRANSACTION_TYPES = [
        (INCOME, 'Начисление'),
        (EXPENSE, 'Списание'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bonus_transactions')
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.type == self.INCOME else '-'
        return f"{sign}{self.amount} бонусов — {self.description}"


class BonusCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(BonusTask, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'task')

    def __str__(self):
        return f"{self.user.username} — {self.task.name}"


class Prize(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название приза")
    description = models.TextField(blank=True, verbose_name="Описание")
    cost = models.PositiveIntegerField(verbose_name="Стоимость (₽)")
    image = models.ImageField(upload_to="prizes/", blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="Доступен для получения")

    def __str__(self):
        return f"{self.name} — {self.cost}₽"


class PrizeRedemption(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='redeemed_prizes')
    prize = models.ForeignKey(Prize, on_delete=models.CASCADE)
    redeemed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} получил {self.prize.name} — {self.redeemed_at.strftime('%d.%m.%Y %H:%M')}"


class QuizQuestion(models.Model):
    task = models.ForeignKey(BonusTask, on_delete=models.CASCADE, related_name="questions")
    question = models.TextField()
    correct_answer = models.CharField(max_length=255)

    def __str__(self):
        return f"Вопрос: {self.question[:50]}..."


class QuizAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    answer = models.CharField(max_length=255)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'question')


class Comment(models.Model):
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    admin_response = models.TextField(blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}"


class Ticket(models.Model):
    reported_comment = models.ForeignKey(
        'Comment',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reports'
    )
    STATUS_CHOICES = [
        ('open', 'Открыт'),
        ('closed', 'Закрыт'),
    ]
    TYPE_CHOICES = [
        ('question', 'Вопрос'),
        ('promotion', 'Повышение статуса'),
        ('report', 'Жалоба на пользователя'),
    ]

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    reported_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                      related_name='reported_tickets')
    comment = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    admin_response = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_type_display()} — {self.created_by.username}"


class OrganizerApplication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organizer_applications')
    passport_series = models.CharField(max_length=10)
    passport_number = models.CharField(max_length=10)
    issued_by = models.CharField(max_length=255)
    date_issued = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    admin_response = models.TextField(blank=True)

    def __str__(self):
        return f"Заявка от {self.user.username} на организатора"


class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.text[:30]}"
