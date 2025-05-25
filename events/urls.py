from django.urls import path
from .views import (
    bonus_task_code_form,
    event_list, event_detail, event_create, event_edit, event_delete,
    stage_create, stage_edit, stage_delete, register_for_event, unregister_from_event,
    toggle_registration, remove_participant, my_events,
    task_list, task_create, task_edit, task_delete, redeem_bonus_code, event_bonus_tasks,
    event_tasks_for_user, complete_event_task, event_user_tasks, submit_event_task_code,
    complete_bonus_task, bonus_task_edit, event_payment,
)


urlpatterns = [
    path('', event_list, name='event-list'),
    path('<int:pk>/', event_detail, name='event-detail'),
    path('create/', event_create, name='event-create'),
    path('<int:pk>/edit/', event_edit, name='event-edit'),
    path('<int:pk>/delete/', event_delete, name='event-delete'),

    path('<int:event_id>/stages/create/', stage_create, name='stage-create'),
    path('stages/<int:stage_id>/edit/', stage_edit, name='stage-edit'),  # Новый маршрут
    path('stages/<int:stage_id>/delete/', stage_delete, name='stage-delete'),

    path('<int:event_id>/register/', register_for_event, name='event-register'),
    path('<int:event_id>/unregister/', unregister_from_event, name='event-unregister'),
    path('events/<int:event_id>/toggle-registration/', toggle_registration, name='toggle-registration'),
    path('<int:event_id>/remove-participant/<int:user_id>/', remove_participant, name='remove-participant'),

    path('my/', my_events, name='my-events'),

    path('<int:event_id>/tasks/', task_list, name='task-list'),
    path('<int:event_id>/tasks/create/', task_create, name='task-create'),
    path('tasks/<int:task_id>/edit/', task_edit, name='task-edit'),
    path('tasks/<int:task_id>/delete/', task_delete, name='task-delete'),
    path("bonus/redeem/", redeem_bonus_code, name="redeem-bonus-code"),
    path('<int:event_id>/bonus-tasks/', event_bonus_tasks, name='event-bonus-tasks'),
    path('<int:event_id>/tasks/available/', event_tasks_for_user, name='event-user-tasks'),
    path('event-task/complete/<int:task_id>/', complete_event_task, name='complete-event-task'),
    path('events/<int:event_id>/tasks/', event_user_tasks, name='event-user-tasks'),
    path('events/<int:event_id>/tasks/<int:task_id>/submit/', submit_event_task_code, name='submit-event-task-code'),
    path('bonus-task/<int:task_id>/complete/', complete_bonus_task, name='complete-bonus-task'),
    path('bonus-tasks/<int:task_id>/edit/', bonus_task_edit, name='bonus-task-edit'),

    path('bonus-tasks/<int:task_id>/redeem/', bonus_task_code_form, name='redeem-bonus-code-form'),
    path('<int:event_id>/payment/', event_payment, name='event-payment'),

]
