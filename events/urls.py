from django.urls import path
from .views import (
    event_list, event_detail, event_create, event_edit, event_delete,
    stage_create, stage_edit, stage_delete, register_for_event, unregister_from_event,
    toggle_registration, remove_participant
)

urlpatterns = [
    path('', event_list, name='event-list'),
    path('<int:pk>/', event_detail, name='event-detail'),
    path('create/', event_create, name='event-create'),
    path('<int:pk>/edit/', event_edit, name='event-edit'),
    path('<int:pk>/delete/', event_delete, name='event-delete'),

    # Маршруты для этапов
    path('<int:event_id>/stages/create/', stage_create, name='stage-create'),
    path('stages/<int:stage_id>/edit/', stage_edit, name='stage-edit'),  # Новый маршрут
    path('stages/<int:stage_id>/delete/', stage_delete, name='stage-delete'),

    # Регистрация на мероприятие
    path('<int:event_id>/register/', register_for_event, name='event-register'),
    path('<int:event_id>/unregister/', unregister_from_event, name='event-unregister'),
    path('events/<int:event_id>/toggle-registration/', toggle_registration, name='toggle-registration'),
    path('<int:event_id>/remove-participant/<int:user_id>/', remove_participant, name='remove-participant'),
]
