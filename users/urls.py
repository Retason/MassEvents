from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, CustomTokenObtainPairView, UserListView,
    UserDetailView, verify_email, wallet_view, wallet_history,
    user_profile, prize_catalog, redeem_prize, my_prizes,
    submit_bonus_code, available_bonus_tasks, bonus_task_public,
    public_bonus_tasks, event_user_tasks, leaderboard_view,
    pass_quiz, bonus_task_create,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('list/', UserListView.as_view(), name='user-list'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('verify-email/<uuid:token>/', verify_email, name='verify-email'),

    path('wallet/', wallet_view, name='wallet'),
    path('wallet/history/', wallet_history, name='wallet-history'),
    path('profile/', user_profile, name='user-profile'),
    path('prizes/', prize_catalog, name='prize-catalog'),
    path('prizes/redeem/<int:prize_id>/', redeem_prize, name='redeem-prize'),
    path('prizes/my/', my_prizes, name='my-prizes'),
    path('bonus-code/submit/', submit_bonus_code, name='submit-bonus-code'),
    path('bonus-tasks/', available_bonus_tasks, name='available-bonus-tasks'),
    path('bonus-task/<str:code>/', bonus_task_public, name='bonus-task-public'),
    path('tasks/', public_bonus_tasks, name='available-tasks'),
    path('event/<int:event_id>/tasks/', event_user_tasks, name='event-user-tasks'),    path('leaders/', leaderboard_view, name='leaderboard'),
    path('quiz/<int:task_id>/', pass_quiz, name='pass-quiz'),
    path('bonus-tasks/create/', bonus_task_create, name='bonus-task-create'),
]
