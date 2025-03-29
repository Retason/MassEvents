from django.contrib import admin
from .models import Event, EventRegistration, EventStage, EventTask, TaskCompletion


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