
from django.contrib import admin
from .models import (
    Event,
    EventRegistration,
    EventStage,
    EventTask,
    TaskCompletion,
    BonusTask,
    BonusTaskCompletion,
)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_time', 'end_time', 'registration_closed', 'organizer')
    list_filter = ('registration_closed',)
    search_fields = ('title', 'description')
    ordering = ('-start_time',)


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'registered_at')
    search_fields = ('user__username', 'event__title')


@admin.register(EventStage)
class EventStageAdmin(admin.ModelAdmin):
    list_display = ('title', 'event', 'start_time', 'end_time')
    ordering = ('event', 'start_time')


@admin.register(EventTask)
class EventTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'event', 'type', 'reward', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('title', 'description', 'code')
    ordering = ('event', 'title')


@admin.register(TaskCompletion)
class TaskCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'submitted_answer', 'completed_at')
    list_filter = ('completed_at',)
    search_fields = ('user__username', 'task__title')


# BonusTask и BonusTaskCompletion НЕ регистрируем повторно, если уже зарегистрированы в другом файле
