from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Event
from .forms import EventForm
from django.contrib import messages
from datetime import datetime


def event_list(request):
    """Выводит список всех мероприятий."""
    events = Event.objects.all()
    return render(request, 'events/event_list.html', {'events': events})


def event_detail(request, pk):
    """Выводит подробную информацию о мероприятии."""
    event = get_object_or_404(Event, pk=pk)
    return render(request, 'events/event_detail.html', {'event': event})


@login_required
def event_create(request):
    """Создаёт новое мероприятие (только для авторизованных пользователей)."""
    if request.method == 'POST':
        print("Данные из POST-запроса:", request.POST)

        # ПРИНУДИТЕЛЬНО КОНВЕРТИРУЕМ ДАТЫ ПЕРЕД СОЗДАНИЕМ ФОРМЫ
        post_data = request.POST.copy()  # Создаём копию данных запроса
        try:
            post_data['start_time'] = datetime.strptime(post_data['start_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
            post_data['end_time'] = datetime.strptime(post_data['end_time'], "%d.%m.%Y, %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            print("Ошибка: неверный формат даты!")
            messages.error(request, "Ошибка: неверный формат даты и времени!")
            return render(request, 'events/event_form.html', {'form': EventForm(request.POST)})

        form = EventForm(post_data)  # Передаём исправленные данные

        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            messages.success(request, "Мероприятие успешно создано!")
            return redirect('event-list')

        else:
            print("Форма невалидна, ошибки:", form.errors)
            messages.error(request, f"Ошибка при создании мероприятия: {form.errors}")

    else:
        form = EventForm()

    return render(request, 'events/event_form.html', {'form': form})


@login_required
def event_edit(request, pk):
    """Редактирование мероприятия (только для организатора)."""
    event = get_object_or_404(Event, pk=pk)

    # Проверяем, что текущий пользователь — организатор
    if request.user != event.organizer:
        messages.error(request, "У вас нет прав для редактирования этого мероприятия.")
        return redirect('event-detail', pk=pk)

    if request.method == 'POST':
        post_data = request.POST.copy()

        # Принудительно исправляем формат даты
        try:
            post_data['start_time'] = datetime.strptime(post_data['start_time'], "%d.%m.%Y, %H:%M").strftime(
                "%Y-%m-%d %H:%M:%S")
            post_data['end_time'] = datetime.strptime(post_data['end_time'], "%d.%m.%Y, %H:%M").strftime(
                "%Y-%m-%d %H:%M:%S")
        except ValueError:
            messages.error(request, "Ошибка: неверный формат даты и времени!")
            return render(request, 'events/event_form.html', {'form': EventForm(post_data), 'is_edit': True})

        form = EventForm(post_data, instance=event)

        if form.is_valid():
            form.save()
            messages.success(request, "Мероприятие успешно обновлено!")
            return redirect('event-detail', pk=pk)
        else:
            messages.error(request, f"Ошибка при обновлении мероприятия: {form.errors}")

    else:
        form = EventForm(instance=event)

    return render(request, 'events/event_form.html', {'form': form, 'is_edit': True})


@login_required
def event_delete(request, pk):
    """Удаление мероприятия (только для организатора)."""
    event = get_object_or_404(Event, pk=pk)

    # Проверяем, что текущий пользователь — организатор
    if request.user != event.organizer:
        messages.error(request, "У вас нет прав для удаления этого мероприятия.")
        return redirect('event-detail', pk=pk)

    event.delete()
    messages.success(request, "Мероприятие успешно удалено.")
    return redirect('event-list')
