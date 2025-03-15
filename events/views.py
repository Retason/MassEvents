from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Event, EventRegistration, EventStage
from .forms import EventForm, EventStageForm
from django.contrib import messages
from datetime import datetime


def event_list(request):
    """Выводит список всех мероприятий."""
    events = Event.objects.all()
    return render(request, 'events/event_list.html', {'events': events})


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)

    # Проверяем, записан ли пользователь
    is_registered = False
    if request.user.is_authenticated:
        is_registered = EventRegistration.objects.filter(user=request.user, event=event).exists()

    context = {
        'event': event,
        'is_registered': is_registered,
        'latitude': event.latitude if event.latitude else 55.751574,  # Москва по умолчанию
        'longitude': event.longitude if event.longitude else 37.573856
    }

    return render(request, 'events/event_detail.html', context)


@login_required
def event_create(request):
    """Создаёт новое мероприятие (только для организаторов и админов)."""

    if not (request.user.is_superuser or request.user.role in ['admin', 'organizer']):
        messages.error(request, "У вас нет прав на создание мероприятия.")
        return redirect('event-list')

    if request.method == 'POST':
        print("Данные из формы:", request.POST)  # Проверяем что приходит в запросе

        # Проверяем, есть ли `end_time` в `POST`-запросе
        if 'end_time' not in request.POST or not request.POST['end_time']:
            print("Ошибка: end_time отсутствует в запросе или пустое!")
            messages.error(request, "Ошибка: Дата окончания мероприятия не передана!")
            return render(request, 'events/event_form.html', {'form': EventForm(request.POST)})

        post_data = request.POST.copy()

        # Пробуем конвертировать дату
        try:
            post_data['start_time'] = datetime.strptime(
                post_data['start_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
            post_data['end_time'] = datetime.strptime(
                post_data['end_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            print("Ошибка: Неверный формат даты!")
            messages.error(request, "Ошибка: неверный формат даты и времени!")
            return render(request, 'events/event_form.html', {'form': EventForm(post_data)})

        print("После обработки:", post_data)  # Вывод обработанных данных

        form = EventForm(post_data)

        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            messages.success(request, "Мероприятие успешно создано!")
            return redirect('event-list')
        else:
            print("Ошибка формы:", form.errors)  # Выводим ошибки формы
            messages.error(request, f"Ошибка при создании мероприятия: {form.errors}")

    else:
        form = EventForm()

    return render(request, 'events/event_form.html', {'form': form})






@login_required
def event_edit(request, pk):
    """Редактирование мероприятия (только для организатора или админа)."""
    event = get_object_or_404(Event, pk=pk)

    # Разрешаем редактирование только организатору мероприятия или админу
    if request.user != event.organizer and not request.user.is_superuser:
        messages.error(request, "У вас нет прав для редактирования этого мероприятия.")
        return redirect('event-detail', pk=pk)

    if request.method == 'POST':
        post_data = request.POST.copy()

        # Принудительно исправляем формат даты
        try:
            post_data['start_time'] = datetime.strptime(
                post_data['start_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
            post_data['end_time'] = datetime.strptime(
                post_data['end_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            messages.error(request, "Ошибка: неверный формат даты и времени!")
            return render(request, 'events/event_form.html', {'form': EventForm(post_data), 'event': event, 'is_edit': True})

        form = EventForm(post_data, instance=event)

        if form.is_valid():
            form.save()
            messages.success(request, "Мероприятие успешно обновлено!")
            return redirect('event-detail', pk=pk)
        else:
            messages.error(request, "Ошибка при обновлении мероприятия.")

    else:
        form = EventForm(instance=event)

    return render(request, 'events/event_form.html', {'form': form, 'event': event, 'is_edit': True})



@login_required
def event_delete(request, pk):
    """Удаляет мероприятие (только для организатора или админа)."""
    event = get_object_or_404(Event, pk=pk)

    # Разрешаем удаление только организатору мероприятия или админу
    if request.user != event.organizer and not request.user.is_superuser:
        messages.error(request, "У вас нет прав на удаление этого мероприятия.")
        return redirect('event-detail', pk=pk)

    event.delete()
    messages.success(request, "Мероприятие успешно удалено.")
    return redirect('event-list')



@login_required
def register_for_event(request, event_id):
    """Записывает пользователя на мероприятие"""
    event = get_object_or_404(Event, id=event_id)

    # Проверяем, записан ли уже пользователь
    if EventRegistration.objects.filter(user=request.user, event=event).exists():
        messages.warning(request, "Вы уже записаны на это мероприятие!")
    else:
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
        print("Полученные данные из формы:", request.POST)

        post_data = request.POST.copy()
        try:
            post_data['start_time'] = datetime.strptime(post_data['start_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
            post_data['end_time'] = datetime.strptime(post_data['end_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            print("Ошибка: неверный формат даты!")
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
            print("Форма невалидна! Ошибки:", form.errors)
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
    event = stage.event  # Получаем мероприятие, к которому относится этап

    # Проверяем права доступа
    if request.user != event.organizer and not request.user.is_superuser:
        messages.error(request, "У вас нет прав для редактирования этого этапа.")
        return redirect('event-detail', pk=event.id)

    if request.method == "POST":
        print("Полученные данные из формы:", request.POST)

        post_data = request.POST.copy()
        try:
            post_data['start_time'] = datetime.strptime(post_data['start_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
            post_data['end_time'] = datetime.strptime(post_data['end_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            print("Ошибка: неверный формат даты!")
            messages.error(request, "Ошибка: неверный формат даты и времени!")
            return render(request, 'events/stage_form.html', {'form': EventStageForm(request.POST), 'event': event, 'stage': stage, 'is_edit': True})

        form = EventStageForm(post_data, instance=stage)

        if form.is_valid():
            form.save()
            messages.success(request, "Этап успешно обновлён!")
            return redirect('event-detail', pk=event.id)
        else:
            print("Форма невалидна! Ошибки:", form.errors)
            messages.error(request, "Ошибка при обновлении этапа. Проверьте введённые данные.")

    else:
        form = EventStageForm(instance=stage)

    return render(request, 'events/stage_form.html', {'form': form, 'event': event, 'stage': stage, 'is_edit': True})
