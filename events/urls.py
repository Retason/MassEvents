from django.urls import path
from .views import event_list, event_detail, event_create, event_edit, event_delete

urlpatterns = [
    path('', event_list, name='event-list'),
    path('<int:pk>/', event_detail, name='event-detail'),
    path('create/', event_create, name='event-create'),
    path('<int:pk>/edit/', event_edit, name='event-edit'),
    path('<int:pk>/delete/', event_delete, name='event-delete'),  # Новый маршрут для удаления
]
