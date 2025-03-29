import openpyxl
from django.views.decorators.http import require_POST
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from openpyxl.utils import get_column_letter
from django.db.models import Count, Sum

from . import serializers

from events.models import EventRegistration, BonusTaskCompletion, Event
from .models import (
    User, WalletTransaction, BonusTask, BonusCompletion,
    Prize, PrizeRedemption,
)
from .serializers import RegisterSerializer, UserSerializer
from .forms import RegisterForm, LoginForm, BonusTaskForm
from .utils import send_verification_email

from decimal import Decimal


# --- API Views ---
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        if not user.is_verified:
            raise serializers.ValidationError("Ваш email не подтверждён. Проверьте почту.")
        token = super().get_token(user)
        token['role'] = user.role
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


User = get_user_model()


# --- Registration with bonus ---
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            send_verification_email(user)

            # 🎁 Попытка выдать бонус за регистрацию
            task = BonusTask.objects.filter(
                type=BonusTask.SYSTEM,
                is_active=True,
                code__isnull=True,
                name__icontains="регистрация"
            ).first()

            if task:
                user.balance += task.reward
                user.save()

                WalletTransaction.objects.create(
                    user=user,
                    amount=task.reward,
                    type=WalletTransaction.INCOME,
                    description="Бонус за регистрацию"
                )
                BonusCompletion.objects.create(user=user, task=task)

            return render(request, "users/verification_sent.html")
    else:
        form = RegisterForm()

    return render(request, "users/register.html", {"form": form})


def verify_email(request, token):
    user = get_object_or_404(User, verification_token=token)
    user.is_verified = True
    user.is_active = True
    user.verification_token = None
    user.save()

    messages.success(request, "Ваш email подтверждён. Теперь можно войти.")
    return redirect("login")


def user_login(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_verified:
                messages.error(request, "Email не подтверждён.")
                return redirect("login")
            login(request, user)
            return redirect("event-list")
    else:
        form = LoginForm()

    return render(request, "users/login.html", {"form": form})


# --- Wallet ---
@login_required
def wallet_view(request):
    transactions = request.user.transactions.all()

    if request.method == "POST":
        try:
            amount = Decimal(request.POST.get("amount"))
            if amount <= 0:
                messages.error(request, "Сумма должна быть положительной.")
            else:
                request.user.balance += amount
                request.user.save()

                WalletTransaction.objects.create(
                    user=request.user,
                    amount=amount,
                    type=WalletTransaction.INCOME,
                    description="Пополнение вручную"
                )
                messages.success(request, f"Баланс пополнен на {amount}₽.")
                return redirect("wallet")
        except (ValueError, TypeError):
            messages.error(request, "Введите корректную сумму.")

    return render(request, "users/wallet.html", {
        "balance": request.user.balance,
        "transactions": transactions
    })


@login_required
def wallet_history(request):
    transactions = WalletTransaction.objects.filter(user=request.user)
    return render(request, 'users/wallet_history.html', {'transactions': transactions})


@login_required
def admin_dashboard(request):
    """Админ-панель с обзором пользователей, транзакций и бонусных задач."""
    if not request.user.is_admin():
        messages.error(request, "Доступ запрещён.")
        return redirect("event-list")

    users_count = User.objects.count()
    transactions_count = WalletTransaction.objects.count()
    bonus_tasks_count = BonusTask.objects.count()

    return render(request, "admin/dashboard.html", {
        "users_count": users_count,
        "transactions_count": transactions_count,
        "bonus_tasks_count": bonus_tasks_count,
    })


@login_required
def manage_bonus_tasks(request):
    """Просмотр и управление бонусными задачами (только для админов)."""
    if not request.user.is_admin():
        messages.error(request, "Доступ запрещён.")
        return redirect("admin-dashboard")

    bonus_tasks = BonusTask.objects.all()

    return render(request, "admin/manage_bonus_tasks.html", {
        "bonus_tasks": bonus_tasks
    })


@login_required
def bonus_task_create(request):
    """Создание бонусного задания, с возможной привязкой к мероприятию."""
    if not request.user.is_admin():
        messages.error(request, "Доступ запрещён.")
        return redirect("manage_bonus_tasks")

    event_id = request.GET.get("event")  # <-- Берём ID мероприятия из URL
    event = None

    if event_id:
        event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        form = BonusTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)

            # Если создаём через мероприятие — привязываем
            if event:
                task.event = event

            task.save()
            messages.success(request, "Бонусное задание создано!")

            # Возврат к списку заданий мероприятия, если задание было привязано
            if event:
                return redirect("event-bonus-tasks", event_id=event.id)

            return redirect("manage_bonus_tasks")
    else:
        form = BonusTaskForm()

    return render(request, "admin/bonus_task_form.html", {
        "form": form,
        "is_edit": False,
        "event": event  # <-- Можно использовать в шаблоне, если нужно
    })


@login_required
def bonus_task_edit(request, task_id):
    """Редактирование бонусного задания."""
    task = get_object_or_404(BonusTask, id=task_id)

    if not request.user.is_admin():
        messages.error(request, "Доступ запрещён.")
        return redirect("manage_bonus_tasks")

    if request.method == "POST":
        form = BonusTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Задание обновлено!")
            return redirect("manage_bonus_tasks")
    else:
        form = BonusTaskForm(instance=task)

    return render(request, "admin/bonus_task_form.html", {"form": form, "is_edit": True, "task": task})


@login_required
def bonus_task_delete(request, task_id):
    """Удаление бонусного задания."""
    task = get_object_or_404(BonusTask, id=task_id)

    if not request.user.is_admin():
        messages.error(request, "Доступ запрещён.")
        return redirect("manage_bonus_tasks")

    task.delete()
    messages.success(request, "Задание удалено.")
    return redirect("manage_bonus_tasks")


@login_required
def user_profile(request):
    """Профиль пользователя: регистрация на события, выполненные задания, баланс."""
    registered_events = EventRegistration.objects.filter(user=request.user).select_related('event')
    bonus_tasks = BonusTaskCompletion.objects.filter(user=request.user).select_related('task')

    return render(request, 'users/profile.html', {
        'registered_events': registered_events,
        'bonus_tasks': bonus_tasks,
        'balance': request.user.balance
    })



def prize_catalog(request):
    """Публичный список призов"""
    prizes = Prize.objects.filter(is_active=True)
    return render(request, 'users/prize_catalog.html', {'prizes': prizes})


@login_required
def redeem_prize(request, prize_id):
    prize = get_object_or_404(Prize, id=prize_id, is_active=True)

    if request.user.balance < prize.cost:
        messages.error(request, "Недостаточно баллов для получения приза.")
        return redirect('prize-catalog')

    # Списываем баллы
    request.user.balance -= prize.cost
    request.user.save()

    # Записываем факт получения
    PrizeRedemption.objects.create(user=request.user, prize=prize)

    # Логируем транзакцию
    WalletTransaction.objects.create(
        user=request.user,
        type=WalletTransaction.EXPENSE,
        amount=prize.cost,
        description=f"Получен приз: {prize.name}"
    )

    messages.success(request, f"Вы получили приз: {prize.name}!")
    return redirect('prize-catalog')


@login_required
def my_prizes(request):
    """Показывает список призов, которые получил пользователь"""
    redemptions = PrizeRedemption.objects.filter(user=request.user).select_related('prize').order_by('-redeemed_at')
    return render(request, 'users/my_prizes.html', {'redemptions': redemptions})


@login_required
@require_POST
def submit_bonus_code(request):
    code = request.POST.get("code", "").strip()

    if not code:
        messages.error(request, "Пожалуйста, введите код.")
        return redirect("user-profile")  # или другую страницу

    try:
        task = BonusTask.objects.get(code__iexact=code, is_active=True)
    except BonusTask.DoesNotExist:
        messages.error(request, "Код недействителен или уже использован.")
        return redirect("user-profile")

    # Проверка: не выполнял ли уже
    if BonusTaskCompletion.objects.filter(user=request.user, task=task).exists():
        messages.info(request, "Вы уже использовали этот код.")
        return redirect("user-profile")

    # Начисляем бонус
    request.user.balance += task.reward
    request.user.save()

    BonusTaskCompletion.objects.create(user=request.user, task=task)
    messages.success(request, f"Поздравляем! Вы получили {task.reward}₽ за задание «{task.name}».")

    return redirect("user-profile")


@login_required
def available_bonus_tasks(request):
    """Список доступных заданий (глобальных и для мероприятий, на которые пользователь записан)"""
    completed_ids = BonusTaskCompletion.objects.filter(user=request.user).values_list('task_id', flat=True)

    # Все мероприятия, на которые пользователь записан
    registered_event_ids = Event.objects.filter(eventregistration__user=request.user).values_list('id', flat=True)

    # 1. Глобальные задания
    global_tasks = BonusTask.objects.filter(is_active=True, event__isnull=True)

    # 2. Задания, привязанные к мероприятиям, на которые пользователь записан
    event_tasks = BonusTask.objects.filter(is_active=True, event_id__in=registered_event_ids)

    all_tasks = (global_tasks | event_tasks).distinct().order_by('-reward')

    return render(request, 'users/available_tasks.html', {
        'tasks': all_tasks,
        'completed_ids': set(completed_ids)
    })


@login_required
def bonus_task_create(request):
    """Создание бонусного задания (с возможной привязкой к мероприятию)."""
    if not request.user.is_admin() and not request.user.is_organizer():
        messages.error(request, "Доступ запрещён.")
        return redirect("event-list")

    event_id = request.GET.get("event")
    event = None

    if event_id:
        from events.models import Event
        event = get_object_or_404(Event, id=event_id)

        # Только организатор этого мероприятия или админ
        if not request.user.is_superuser and event.organizer != request.user:
            messages.error(request, "У вас нет прав на добавление задания к этому мероприятию.")
            return redirect("event-detail", pk=event.id)

    if request.method == "POST":
        form = BonusTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.event = event  # ← Привязываем мероприятие, если было передано
            task.save()
            messages.success(request, "Бонусное задание создано!")
            if event:
                return redirect("event-bonus-tasks", event_id=event.id)
            return redirect("manage_bonus_tasks")
    else:
        form = BonusTaskForm()

    return render(request, "admin/bonus_task_form.html", {
        "form": form,
        "is_edit": False,
        "event": event
    })


@login_required
def bonus_task_public(request, code):
    try:
        task = BonusTask.objects.get(code__iexact=code, is_active=True)
    except BonusTask.DoesNotExist:
        messages.error(request, "Задание не найдено или недействительно.")
        return redirect("event-list")

    already_done = BonusTaskCompletion.objects.filter(user=request.user, task=task).exists()

    if request.method == "POST" and not already_done:
        # Начисляем баллы
        request.user.balance += task.reward
        request.user.save()

        BonusTaskCompletion.objects.create(user=request.user, task=task)
        messages.success(request, f"Вы получили {task.reward}₽ за выполнение задания!")
        return redirect("bonus-task-public", code=code)

    return render(request, "users/bonus_task_public.html", {
        "task": task,
        "already_done": already_done
    })


def public_bonus_tasks(request):
    """Показывает активные задания с QR-кодами (публично)."""
    tasks = BonusTask.objects.filter(is_active=True, code__isnull=False)
    return render(request, 'users/available_tasks.html', {'tasks': tasks})


@login_required
def event_user_tasks(request, event_id):
    """Показывает задания для мероприятия и статус их выполнения текущим пользователем."""
    event = get_object_or_404(Event, id=event_id)

    if not event.enable_tasks:
        messages.warning(request, "На этом мероприятии система заданий отключена.")
        return redirect('event-detail', pk=event_id)

    tasks = BonusTask.objects.filter(event=event, is_active=True)
    completed_ids = BonusTaskCompletion.objects.filter(user=request.user, task__in=tasks).values_list('task_id', flat=True)

    return render(request, 'users/event_tasks.html', {
        'event': event,
        'tasks': tasks,
        'completed_ids': set(completed_ids),
    })


@login_required
def task_completions_view(request, task_id):
    task = get_object_or_404(BonusTask, id=task_id)
    User = get_user_model()

    # Защита: только организатор задания или админ
    if task.event:
        is_owner = task.event.organizer == request.user
    else:
        is_owner = request.user.is_admin()

    if not (is_owner or request.user.is_superuser):
        messages.error(request, "У вас нет доступа к просмотру этого задания.")
        return redirect("event-list")

    completions = BonusTaskCompletion.objects.filter(task=task).select_related("user").order_by("-completed_at")

    return render(request, "admin/task_completions.html", {
        "task": task,
        "completions": completions,
    })


@login_required
def export_task_completions_xlsx(request, task_id):
    task = get_object_or_404(BonusTask, id=task_id)

    # Доступ только организатору или админу
    if task.event:
        is_owner = task.event.organizer == request.user
    else:
        is_owner = request.user.is_admin()

    if not (is_owner or request.user.is_superuser):
        messages.error(request, "У вас нет доступа к этому заданию.")
        return redirect("event-list")

    completions = BonusTaskCompletion.objects.filter(task=task).select_related("user").order_by("completed_at")

    # Создание Excel-файла
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Выполнения"

    # Заголовки
    headers = ["Имя пользователя", "Email", "Баланс (₽)", "Дата выполнения"]
    ws.append(headers)

    # Данные
    for comp in completions:
        ws.append([
            comp.user.username,
            comp.user.email,
            float(comp.user.balance),
            comp.completed_at.strftime("%d.%m.%Y %H:%M"),
        ])

    # Ширина колонок
    for col_num, column_title in enumerate(headers, 1):
        column_letter = get_column_letter(col_num)
        ws.column_dimensions[column_letter].width = 20

    # Ответ пользователю
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    filename = f"{task.name.replace(' ', '_')}_выполнения.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)

    return response


@login_required
def export_event_completions_xlsx(request, event_id):
    from events.models import BonusTask, BonusTaskCompletion

    event = get_object_or_404(Event, id=event_id)

    if request.user != event.organizer and not request.user.is_superuser:
        messages.error(request, "У вас нет доступа к этому мероприятию.")
        return redirect("event-detail", pk=event.id)

    tasks = BonusTask.objects.filter(event=event)
    completions = BonusTaskCompletion.objects.filter(task__in=tasks).select_related("user", "task").order_by("task__name", "completed_at")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Все выполнения"

    headers = ["Задание", "Пользователь", "Email", "Награда (₽)", "Дата выполнения"]
    ws.append(headers)

    for c in completions:
        ws.append([
            c.task.name,
            c.user.username,
            c.user.email,
            float(c.task.reward),
            c.completed_at.strftime("%d.%m.%Y %H:%M"),
        ])

    # Автоматическая ширина колонок
    for col_num, column_title in enumerate(headers, 1):
        ws.column_dimensions[get_column_letter(col_num)].width = 25

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    filename = f"{event.title.replace(' ', '_')}_выполнения.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)

    return response


def leaderboard_view(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Получаем пользователей с количеством выполнений и суммой баллов
    users = User.objects.annotate(
        total_tasks=Count('bonustaskcompletion'),
        total_balance=Sum('balance')
    ).order_by('-balance', '-total_tasks')[:20]

    return render(request, 'users/leaderboard.html', {
        'leaders': users,
    })
