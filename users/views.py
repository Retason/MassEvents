from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from . import serializers
from .models import User
from .serializers import RegisterSerializer, UserSerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, get_user_model
from .forms import RegisterForm, LoginForm
from .utils import send_verification_email
from django.contrib import messages


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        if not user.is_verified:  # Запрещаем вход неподтверждённым пользователям
            raise serializers.ValidationError("Ваш email не подтверждён. Проверьте почту.")

        token = super().get_token(user)
        token['role'] = user.role  # Добавляем роль в токен
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]  # Только для админа


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]  # Только для админа


User = get_user_model()


def register(request):
    """Регистрация нового пользователя с подтверждением email"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Блокируем вход до подтверждения email
            user.save()

            print(f"[DEBUG] Новый пользователь: {user.username} ({user.email})")
            send_verification_email(user)

            return render(request, "users/verification_sent.html")

        print("[ERROR] Ошибка валидации формы:", form.errors)

    else:
        form = RegisterForm()

    return render(request, "users/register.html", {"form": form})


def verify_email(request, token):
    """Подтверждает email по токену"""
    user = get_object_or_404(User, verification_token=token)
    user.is_verified = True
    user.is_active = True
    user.verification_token = None  # Очищаем токен
    user.save()

    messages.success(request, "Ваш email успешно подтверждён! Теперь можно войти.")
    return redirect("login")


def user_login(request):
    """Авторизация только подтверждённых пользователей"""
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_verified:
                messages.error(request, "Ваш email не подтверждён. Проверьте почту.")
                return redirect("login")

            login(request, user)
            return redirect("event-list")
    else:
        form = LoginForm()

    return render(request, "users/login.html", {"form": form})
