from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from users.models import WalletTransaction
from users.forms import BonusTaskForm
from .models import (Event, EventRegistration, EventStage, EventTask, TaskCompletion,
                     BonusTask, BonusTaskCompletion,)
from .forms import EventForm, EventStageForm
from django.contrib import messages
from datetime import datetime
from django.utils.timezone import now


def parse_datetime(date_str):
    try:
        return datetime.strptime(date_str, "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def event_list(request):
    Event.close_expired_registrations()

    events = Event.objects.filter(is_published=True)
    search_query = request.GET.get('search', '')
    date_filter = request.GET.get('date', '')
    status_filter = request.GET.get('status', '')
    location_filter = request.GET.get('location', '')
    only_my = request.GET.get('only_my') == 'on'

    if search_query:
        events = events.filter(title__icontains=search_query)

    if date_filter:
        events = events.filter(start_time__date=date_filter)

    if status_filter == 'open':
        events = events.filter(registration_closed=False, start_time__gte=now())
    elif status_filter == 'closed':
        events = events.filter(registration_closed=True)
    elif status_filter == 'finished':
        events = events.filter(start_time__lt=now())

    if location_filter:
        events = events.filter(location__icontains=location_filter)

    if only_my and request.user.is_authenticated:
        registered_ids = EventRegistration.objects.filter(user=request.user).values_list('event_id', flat=True)
        events = events.filter(id__in=registered_ids)

    return render(request, 'events/event_list.html', {
        'events': events,
        'search_query': search_query,
        'date_filter': date_filter,
        'status_filter': status_filter,
        'location_filter': location_filter,
        'only_my': only_my,
    })


def event_detail(request, pk):
    from users.forms import CommentForm
    event = get_object_or_404(Event, pk=pk)

    event.check_and_close_registration()

    is_registered = False

    if request.user.is_authenticated:
        is_registered = EventRegistration.objects.filter(user=request.user, event=event).exists()

        event_tasks = EventTask.objects.filter(event=event, is_active=True)
        bonus_tasks = BonusTask.objects.filter(event=event, is_active=True)

        completed_event_tasks = TaskCompletion.objects.filter(
            user=request.user, task__in=event_tasks
        ).values_list('task_id', flat=True)

        completed_bonus_tasks = BonusTaskCompletion.objects.filter(
            user=request.user, task__in=bonus_tasks
        ).values_list('task_id', flat=True)
    else:
        event_tasks = []
        bonus_tasks = []
        completed_event_tasks = []
        completed_bonus_tasks = []

    comments = event.comments.filter(parent__isnull=True).prefetch_related('replies', 'user')
    form = CommentForm()
    if request.method == 'POST' and 'content' in request.POST:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.event = event
            comment.user = request.user
            parent_id = request.POST.get('parent_id')
            if parent_id:
                comment.parent_id = int(parent_id)
            comment.save()
            return redirect('event-detail', pk=pk)

    context = {
        'event': event,
        'is_registered': is_registered,
        'latitude': event.latitude if event.latitude else 55.751574,
        'longitude': event.longitude if event.longitude else 37.573856,
        'event_tasks': event_tasks,
        'bonus_tasks': bonus_tasks,
        'completed_event_task_ids': set(completed_event_tasks),
        'completed_bonus_task_ids': set(completed_bonus_tasks),
        'comment_form': form,
        'comments': comments,
    }

    return render(request, 'events/event_detail.html', context)


@login_required
def event_create(request):
    if not (request.user.is_superuser or request.user.role in ['admin', 'organizer']):
        messages.error(request, "У вас нет прав на создание мероприятия.")
        return redirect('event-list')

    if request.method == 'POST':
        post_data = request.POST.copy()
        files_data = request.FILES

        try:
            post_data['start_time'] = datetime.strptime(
                post_data['start_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
            post_data['end_time'] = datetime.strptime(
                post_data['end_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:

            messages.error(request, "Ошибка: неверный формат даты и времени!")
            return render(request, 'events/event_form.html', {'form': EventForm(post_data)})

        form = EventForm(post_data, files_data)

        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user

            event.latitude = post_data.get('latitude') or None
            event.longitude = post_data.get('longitude') or None

            event.save()
            messages.success(request, "Мероприятие успешно создано!")
            return redirect('event-list')
        else:

            messages.error(request, f"Ошибка при создании мероприятия: {form.errors}")

    else:
        form = EventForm()

    return render(request, 'events/event_form.html', {'form': form})


@login_required
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if request.user != event.organizer and not request.user.is_superuser:
        messages.error(request, "У вас нет прав для редактирования этого мероприятия.")
        return redirect('event-detail', pk=pk)

    if request.method == 'POST':
        post_data = request.POST.copy()

        try:
            post_data['start_time'] = datetime.strptime(
                post_data['start_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
            post_data['end_time'] = datetime.strptime(
                post_data['end_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            messages.error(request, "Ошибка: неверный формат даты и времени!")
            return render(request, 'events/event_form.html', {'form': EventForm(post_data), 'event': event, 'is_edit': True})

        form = EventForm(post_data, request.FILES, instance=event)

        if form.is_valid():
            form.save()
            messages.success(request, "Мероприятие успешно обновлено!")
            return redirect('event-detail', pk=pk)
        else:
            messages.error(request, "Ошибка при обновлении мероприятия.")

    else:
        formatted_start_time = event.start_time.strftime('%d.%m.%Y, %H:%M') if event.start_time else ''
        formatted_end_time = event.end_time.strftime('%d.%m.%Y, %H:%M') if event.end_time else ''

        form = EventForm(instance=event, initial={
            'start_time': formatted_start_time,
            'end_time': formatted_end_time,
            'location': event.location,
        })

    return render(request, 'events/event_form.html', {'form': form, 'event': event, 'is_edit': True})


@login_required
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if request.user != event.organizer and not request.user.is_superuser:
        messages.error(request, "У вас нет прав на удаление этого мероприятия.")
        return redirect('event-detail', pk=pk)

    event.delete()
    messages.success(request, "Мероприятие успешно удалено.")
    return redirect('event-list')


@login_required
def register_for_event(request, event_id):
    """Записывает пользователя на мероприятие, если есть места, регистрация открыта и хватает средств"""
    event = get_object_or_404(Event, id=event_id)

    if not event.is_registration_open():
        messages.error(request, "Регистрация на это мероприятие закрыта.")
        return redirect('event-detail', pk=event_id)

    if EventRegistration.objects.filter(user=request.user, event=event).exists():
        messages.warning(request, "Вы уже записаны на это мероприятие!")
    else:
        if event.price > 0:
            if request.user.balance < event.price:
                messages.error(request, f"Недостаточно средств. Требуется {event.price}₽.")
                return redirect('event-detail', pk=event_id)

            request.user.balance -= event.price
            request.user.save()

            WalletTransaction.objects.create(
                user=request.user,
                amount=event.price,
                type=WalletTransaction.EXPENSE,
                description=f"Оплата за участие в мероприятии: {event.title}"
            )

        EventRegistration.objects.create(user=request.user, event=event)
        messages.success(request, "Вы успешно записались на мероприятие!")

    return redirect('event-detail', pk=event_id)


@login_required
def unregister_from_event(request, event_id):
    """Отменяет запись пользователя на мероприятие"""
    event = get_object_or_404(Event, id=event_id)
    registration = EventRegistration.objects.filter(user=request.user, event=event)

    if registration.exists():
        registration.delete()
        messages.success(request, "Вы успешно отменили запись на мероприятие!")
    else:
        messages.warning(request, "Вы не записаны на это мероприятие!")

    return redirect('event-detail', pk=event_id)


@login_required
def stage_create(request, event_id):
    """Добавление нового этапа в мероприятие."""
    event = get_object_or_404(Event, id=event_id)

    if request.user != event.organizer and not request.user.is_superuser:
        messages.error(request, "У вас нет прав для добавления этапов.")
        return redirect('event-detail', pk=event_id)

    if request.method == "POST":

        post_data = request.POST.copy()
        try:
            post_data['start_time'] = datetime.strptime(post_data['start_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
            post_data['end_time'] = datetime.strptime(post_data['end_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:

            messages.error(request, "Ошибка: неверный формат даты и времени!")
            return render(request, 'events/stage_form.html', {'form': EventStageForm(request.POST), 'event': event})

        form = EventStageForm(post_data)

        if form.is_valid():
            stage = form.save(commit=False)
            stage.event = event
            stage.save()
            messages.success(request, "Этап успешно добавлен!")
            return redirect('event-detail', pk=event_id)
        else:

            messages.error(request, "Ошибка при добавлении этапа. Проверьте введённые данные.")
    else:
        form = EventStageForm()

    return render(request, 'events/stage_form.html', {'form': form, 'event': event})


@login_required
def stage_delete(request, stage_id):
    """Удаление этапа мероприятия."""
    stage = get_object_or_404(EventStage, id=stage_id)

    if request.user != stage.event.organizer and not request.user.is_superuser:
        messages.error(request, "У вас нет прав для удаления этого этапа.")
        return redirect('event-detail', pk=stage.event.id)

    stage.delete()
    messages.success(request, "Этап успешно удалён!")
    return redirect('event-detail', pk=stage.event.id)


@login_required
def stage_edit(request, stage_id):
    """Редактирование этапа мероприятия (только для организатора или админа)."""
    stage = get_object_or_404(EventStage, id=stage_id)
    event = stage.event

    if request.user != event.organizer and not request.user.is_superuser:
        messages.error(request, "У вас нет прав для редактирования этого этапа.")
        return redirect('event-detail', pk=event.id)

    if request.method == "POST":
        post_data = request.POST.copy()

        try:
            post_data['start_time'] = datetime.strptime(
                post_data['start_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
            post_data['end_time'] = datetime.strptime(
                post_data['end_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            messages.error(request, "Неверный формат даты и времени.")
            return render(request, 'events/stage_form.html', {
                'form': EventStageForm(post_data),
                'event': event,
                'stage': stage,
                'is_edit': True
            })

        form = EventStageForm(post_data, instance=stage)
        if form.is_valid():
            form.save()
            messages.success(request, "Этап успешно обновлён!")
            return redirect('event-detail', pk=event.id)
        else:
            messages.error(request, "Ошибка при обновлении этапа.")

    else:
        stage.start_time = stage.start_time.strftime("%d.%m.%Y, %H:%M") if stage.start_time else ''
        stage.end_time = stage.end_time.strftime("%d.%m.%Y, %H:%M") if stage.end_time else ''

        form = EventStageForm(instance=stage)

    return render(request, 'events/stage_form.html', {
        'form': form,
        'event': event,
        'stage': stage,
        'is_edit': True
    })


@login_required
def toggle_registration(request, event_id):
    """Позволяет организатору или администратору вручную закрывать или открывать регистрацию"""
    event = get_object_or_404(Event, id=event_id)

    if request.user != event.organizer and not request.user.is_superuser:
        messages.error(request, "У вас нет прав на изменение регистрации.")
        return redirect('event-detail', pk=event.id)

    event.registration_closed = not event.registration_closed
    event.save()

    if event.registration_closed:
        messages.success(request, "Регистрация на мероприятие закрыта.")
    else:
        messages.success(request, "Регистрация на мероприятие открыта.")

    return redirect('event-detail', pk=event.id)


@login_required
def remove_participant(request, event_id, user_id):
    """Удаляет участника с мероприятия (только организатор или админ)"""
    event = get_object_or_404(Event, id=event_id)
    participant = get_object_or_404(EventRegistration, event=event, user_id=user_id)

    if participant.remove_registration(request.user):
        messages.success(request, f"Пользователь {participant.user.username} удалён с мероприятия.")
    else:
        messages.error(request, "Вы не можете удалить этого пользователя.")

    return redirect('event-detail', pk=event_id)


@login_required
def my_events(request):
    """Показывает мероприятия, созданные текущим пользователем"""
    if not request.user.is_organizer() and not request.user.is_superuser:
        messages.error(request, "У вас нет доступа к этой странице.")
        return redirect('event-list')

    events = Event.objects.filter(organizer=request.user).order_by('-start_time')
    return render(request, 'events/my_events.html', {'events': events})


@login_required
def task_list(request, event_id):
    """Список заданий, связанных с мероприятием"""
    event = get_object_or_404(Event, id=event_id)

    if request.user != event.organizer and not request.user.is_superuser:
        messages.error(request, "Нет доступа к заданиям этого мероприятия.")
        return redirect('event-detail', pk=event.id)

    tasks = BonusTask.objects.filter(event=event)
    return render(request, 'events/task_list.html', {'event': event, 'tasks': tasks})


@login_required
def task_create(request, event_id):
    """Создание задания для мероприятия"""
    event = get_object_or_404(Event, id=event_id)

    if request.user != event.organizer and not request.user.is_superuser:
        messages.error(request, "Нет доступа для создания задания.")
        return redirect('event-detail', pk=event.id)

    if request.method == "POST":
        form = BonusTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.event = event
            task.save()
            messages.success(request, "Задание добавлено!")
            return redirect('task-list', event_id=event.id)
    else:
        form = BonusTaskForm()

    return render(request, 'events/task_form.html', {'form': form, 'event': event, 'is_edit': False})


@login_required
def task_edit(request, task_id):
    """Редактирование задания"""
    task = get_object_or_404(BonusTask, id=task_id)
    event = task.event

    if request.user != event.organizer and not request.user.is_superuser:
        messages.error(request, "Нет прав для редактирования задания.")
        return redirect('event-detail', pk=event.id)

    if request.method == "POST":
        form = BonusTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Задание обновлено.")
            return redirect('task-list', event_id=event.id)
    else:
        form = BonusTaskForm(instance=task)

    return render(request, 'events/task_form.html', {'form': form, 'event': event, 'is_edit': True})


@login_required
def task_delete(request, task_id):
    """Удаление задания"""
    task = get_object_or_404(BonusTask, id=task_id)
    event = task.event

    if request.user != event.organizer and not request.user.is_superuser:
        messages.error(request, "Нет прав на удаление.")
        return redirect('event-detail', pk=event.id)

    task.delete()
    messages.success(request, "Задание удалено.")
    return redirect('task-list', event_id=event.id)


@login_required
def redeem_bonus_code(request):
    if request.method == "POST":
        code = request.POST.get("code", "").strip()

        try:
            task = BonusTask.objects.get(code=code, is_active=True)
            if task.admin_only and not request.user.is_superuser:
                messages.error(request, "Этот код недоступен для обычных пользователей.")
                return redirect("event-list")
        except BonusTask.DoesNotExist:
            messages.error(request, "Неверный или неактивный бонус-код.")
            return redirect("event-list")

        if BonusTaskCompletion.objects.filter(user=request.user, task=task).exists():
            messages.warning(request, "Вы уже использовали этот код.")
            return redirect("event-list")

        BonusTaskCompletion.objects.create(user=request.user, task=task)

        request.user.balance += task.reward
        request.user.save()

        messages.success(request, f"Код принят! Вы получили {task.reward} ₽")
        return redirect("event-list")

    return render(request, "events/redeem_code.html")


@login_required
def event_bonus_tasks(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.user != event.organizer and not request.user.is_superuser:
        messages.error(request, "У вас нет доступа к заданиям этого мероприятия.")
        return redirect('event-detail', pk=event.id)

    tasks = BonusTask.objects.filter(event=event)
    return render(request, 'events/event_bonus_tasks.html', {
        'event': event,
        'tasks': tasks
    })


@login_required
def event_tasks_for_user(request, event_id):
    """Отображает задания для участника мероприятия"""
    event = get_object_or_404(Event, id=event_id)

    is_registered = (
            request.user == event.organizer
            or EventRegistration.objects.filter(user=request.user, event=event).exists()
    )

    if not is_registered and not request.user.is_superuser:
        messages.error(request, "Вы не записаны на это мероприятие.")
        return redirect("event-detail", pk=event.id)

    if not event.enable_tasks:
        messages.warning(request, "Для этого мероприятия задания отключены.")
        return redirect("event-detail", pk=event.id)

    tasks = BonusTask.objects.filter(event=event, is_active=True)
    completed_ids = BonusTaskCompletion.objects.filter(user=request.user, task__in=tasks).values_list('task_id', flat=True)

    return render(request, "events/event_user_tasks.html", {
        "event": event,
        "tasks": tasks,
        "completed_ids": set(completed_ids),
    })


@login_required
@require_POST
def complete_event_task(request, task_id):
    task = get_object_or_404(BonusTask, id=task_id, event__isnull=False, is_active=True)

    if BonusTaskCompletion.objects.filter(user=request.user, task=task).exists():
        messages.info(request, "Вы уже выполнили это задание.")
    else:
        request.user.balance += task.reward
        request.user.save()

        BonusTaskCompletion.objects.create(user=request.user, task=task)

        WalletTransaction.objects.create(
            user=request.user,
            amount=task.reward,
            type=WalletTransaction.INCOME,
            description=f"Бонус за задание: {task.name}"
        )

        messages.success(request, f"Задание «{task.name}» выполнено! +{task.reward}₽")

    return redirect('event-detail', pk=task.event.id)


@login_required
def event_user_tasks(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not EventRegistration.objects.filter(event=event, user=request.user).exists():
        messages.error(request, "Вы не зарегистрированы на это мероприятие.")
        return redirect('event-detail', pk=event_id)

    event_tasks = EventTask.objects.filter(event=event, is_active=True)
    bonus_tasks = BonusTask.objects.filter(event=event, is_active=True)

    completed_event_tasks = TaskCompletion.objects.filter(
        user=request.user, task__in=event_tasks
    ).values_list('task_id', flat=True)

    completed_bonus_tasks = BonusTaskCompletion.objects.filter(
        user=request.user, task__in=bonus_tasks
    ).values_list('task_id', flat=True)

    return render(request, 'events/event_user_tasks.html', {
        'event': event,
        'event_tasks': event_tasks,
        'bonus_tasks': bonus_tasks,
        'completed_event_task_ids': set(completed_event_tasks),
        'completed_bonus_task_ids': set(completed_bonus_tasks),
    })


@require_POST
@login_required
def submit_event_task_code(request, event_id, task_id):
    event = get_object_or_404(Event, id=event_id)
    task = get_object_or_404(EventTask, id=task_id, event=event, is_active=True)

    if not EventRegistration.objects.filter(event=event, user=request.user).exists():
        messages.error(request, "Вы не зарегистрированы на это мероприятие.")
        return redirect('event-detail', pk=event_id)

    if TaskCompletion.objects.filter(user=request.user, task=task).exists():
        messages.info(request, "Вы уже выполнили это задание.")
        return redirect('event-user-tasks', event_id=event.id)

    code = request.POST.get("code", "").strip()
    if code.lower() != task.code.lower():
        messages.error(request, "Неверный код.")
        return redirect('event-user-tasks', event_id=event.id)

    request.user.balance += task.reward
    request.user.save()

    TaskCompletion.objects.create(user=request.user, task=task)

    WalletTransaction.objects.create(
        user=request.user,
        amount=task.reward,
        type=WalletTransaction.INCOME,
        description=f"Награда за задание: {task.name}"
    )

    messages.success(request, f"Задание «{task.name}» выполнено! +{task.reward} ₽")
    return redirect('event-user-tasks', event_id=event.id)


@login_required
@require_POST
def complete_bonus_task(request, task_id):
    task = get_object_or_404(BonusTask, id=task_id)

    if not EventRegistration.objects.filter(user=request.user, event=task.event).exists():
        messages.error(request, "Вы не зарегистрированы на мероприятие.")
        return redirect('event-detail', pk=task.event.id)

    if not task.is_active:
        messages.error(request, "Это задание неактивно.")
    elif BonusTaskCompletion.objects.filter(user=request.user, task=task).exists():
        messages.info(request, "Вы уже выполнили это задание.")
    else:
        request.user.balance += task.reward
        request.user.save()

        BonusTaskCompletion.objects.create(user=request.user, task=task)

        WalletTransaction.objects.create(
            user=request.user,
            amount=task.reward,
            type=WalletTransaction.INCOME,
            description=f"Бонус за задание: {task.name}"
        )

        messages.success(request, f"Вы выполнили бонусное задание и получили {task.reward}₽!")

    return redirect('event-user-tasks', event_id=task.event.id)

@login_required
def bonus_task_edit(request, task_id):
    task = get_object_or_404(BonusTask, id=task_id)

    if not request.user.is_admin() and (not task.event or task.event.organizer != request.user):
        messages.error(request, "Нет доступа к редактированию.")
        return redirect("event-list")

    if request.method == "POST":
        form = BonusTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Бонусное задание обновлено!")
            if task.event:
                return redirect("event-bonus-tasks", event_id=task.event.id)
            return redirect("manage_bonus_tasks")
    else:
        form = BonusTaskForm(instance=task)

    return render(request, "admin/bonus_task_form.html", {
        "form": form,
        "is_edit": True,
        "task": task
    })


@login_required
def bonus_task_code_form(request, task_id):
    task = get_object_or_404(BonusTask, id=task_id, is_active=True)
    if task.admin_only and not request.user.is_superuser:
        messages.error(request, "Этот код недоступен для обычных пользователей.")
        return redirect("event-list")

    if not task.event:
        messages.error(request, "Это задание не связано с мероприятием.")
        return redirect("event-list")

    if not EventRegistration.objects.filter(user=request.user, event=task.event).exists():
        messages.error(request, "Вы не зарегистрированы на это мероприятие.")
        return redirect("event-detail", pk=task.event.id)

    if request.method == "POST":
        if BonusTaskCompletion.objects.filter(user=request.user, task=task).exists():
            messages.info(request, "Вы уже выполнили это задание.")
            return redirect("event-detail", pk=task.event.id)

        code = request.POST.get("code", "").strip()
        if code.lower() != (task.code or "").lower():
            messages.error(request, "Неверный код.")
            return redirect("redeem-bonus-code-form", task_id=task.id)

        request.user.balance += task.reward
        request.user.save()

        BonusTaskCompletion.objects.create(user=request.user, task=task)

        WalletTransaction.objects.create(
            user=request.user,
            amount=task.reward,
            type=WalletTransaction.INCOME,
            description=f"Бонус за задание: {task.name}"
        )

        messages.success(request, f"Задание выполнено! +{task.reward}₽")
        return redirect("event-detail", pk=task.event.id)

    return render(request, "events/bonus_code_form.html", {"task": task})


@login_required
def event_payment(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if EventRegistration.objects.filter(user=request.user, event=event).exists():
        messages.info(request, "Вы уже зарегистрированы.")
        return redirect('event-detail', pk=event.id)

    if request.method == "POST":
        method = request.POST.get("method")

        if method == "wallet":
            if request.user.wallet_balance < event.price:
                messages.error(request, "Недостаточно средств на кошельке.")
                return redirect('event-payment', event_id=event.id)

            request.user.wallet_balance -= event.price
            request.user.save()

            WalletTransaction.objects.create(
                user=request.user,
                amount=event.price,
                type=WalletTransaction.EXPENSE,
                description=f"Оплата за участие в мероприятии: {event.title}"
            )

        elif method == "bonus":
            if request.user.bonus_balance < event.price:
                messages.error(request, "Недостаточно бонусов.")
                return redirect('event-payment', event_id=event.id)

            request.user.bonus_balance -= event.price
            request.user.save()

            from users.models import BonusTransaction
            BonusTransaction.objects.create(
                user=request.user,
                amount=event.price,
                type=BonusTransaction.EXPENSE,
                description=f"Оплата за участие в мероприятии: {event.title}"
            )

        else:
            messages.error(request, "Некорректный способ оплаты.")
            return redirect('event-payment', event_id=event.id)

        EventRegistration.objects.create(user=request.user, event=event)
        messages.success(request, "Вы успешно зарегистрированы!")
        return redirect('event-detail', pk=event.id)

    if request.method == "POST":
        # пока один способ, но структура под расширение
        method = request.POST.get("method")
        if method == "wallet":
            if request.user.balance < event.price:
                messages.error(request, "Недостаточно средств на балансе.")
                return redirect('event-payment', event_id=event.id)

            request.user.balance -= event.price
            request.user.save()

            WalletTransaction.objects.create(
                user=request.user,
                amount=event.price,
                type=WalletTransaction.EXPENSE,
                description=f"Оплата за участие в мероприятии: {event.title}"
            )

        EventRegistration.objects.create(user=request.user, event=event)
        messages.success(request, "Вы успешно зарегистрированы!")
        return redirect('event-detail', pk=event.id)

    return render(request, "events/payment_form.html", {"event": event})


@login_required
def toggle_publish(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.user != event.organizer and not request.user.is_superuser:
        messages.error(request, "Нет доступа.")
        return redirect('event-detail', pk=event_id)
    event.is_published = not event.is_published
    event.save()
    EventRegistration.objects.get_or_create(user=request.user, event=event)
    status = "опубликовано" if event.is_published else "снято с публикации"
    messages.success(request, f"Мероприятие {status}.")
    return redirect('event-detail', pk=event_id)
