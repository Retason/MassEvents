from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views  # Импортируем auth_views!
from users.views import register  # Добавляем представление регистрации

urlpatterns = [
    path('admin/', admin.site.urls),

    # API маршруты
    path('api/users/', include('users.urls')),  # API пользователей
    path('api/events/', include('events.urls')),  # API мероприятий

    # HTML маршруты для мероприятий
    path('events/', include('events.urls')),

    # Аутентификация пользователей
    path('accounts/register/', register, name='register'),  # Регистрация
    path('accounts/login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
]
