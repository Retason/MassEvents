from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, CustomTokenObtainPairView, UserListView,
    UserDetailView, verify_email, wallet_view, wallet_history,
    admin_dashboard, manage_bonus_tasks, bonus_task_create, bonus_task_edit,
    bonus_task_delete, user_profile, prize_catalog, redeem_prize, my_prizes,
    submit_bonus_code, available_bonus_tasks, bonus_task_public,
    public_bonus_tasks, event_user_tasks, task_completions_view, export_task_completions_xlsx,
    export_event_completions_xlsx, leaderboard_view,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('list/', UserListView.as_view(), name='user-list'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('verify-email/<uuid:token>/', verify_email, name='verify-email'),

    # 💰й Страница кошелька
    path('wallet/', wallet_view, name='wallet'),
    path('wallet/history/', wallet_history, name='wallet-history'),

    path('admin/dashboard/', admin_dashboard, name='admin-dashboard'),
    path('admin/bonus-tasks/', manage_bonus_tasks, name='manage_bonus_tasks'),
    path('admin/bonus-tasks/create/', bonus_task_create, name='bonus-task-create'),
    path('admin/bonus-tasks/edit/<int:task_id>/', bonus_task_edit, name='bonus-task-edit'),
    path('admin/bonus-tasks/delete/<int:task_id>/', bonus_task_delete, name='bonus-task-delete'),

    path('profile/', user_profile, name='user-profile'),
    path('prizes/', prize_catalog, name='prize-catalog'),
    path('prizes/redeem/<int:prize_id>/', redeem_prize, name='redeem-prize'),
    path('prizes/my/', my_prizes, name='my-prizes'),
    path('bonus-code/submit/', submit_bonus_code, name='submit-bonus-code'),
    path('bonus-tasks/', available_bonus_tasks, name='available-bonus-tasks'),
    path('bonus-task/<str:code>/', bonus_task_public, name='bonus-task-public'),
    path('tasks/', public_bonus_tasks, name='available-tasks'),
    path('event/<int:event_id>/tasks/', event_user_tasks, name='event-user-tasks'),
    path('admin/bonus-tasks/<int:task_id>/completions/', task_completions_view, name='task-completions'),
    path('admin/bonus-tasks/<int:task_id>/export/', export_task_completions_xlsx, name='task-completions-export'),
    path('admin/events/<int:event_id>/export/', export_event_completions_xlsx, name='event-completions-export'),
    path('leaders/', leaderboard_view, name='leaderboard'),

]
