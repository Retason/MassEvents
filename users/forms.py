from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES[1:], required=True, label="Выберите роль")

    class Meta:
        model = User
        fields = ["username", "email", "role", "password1", "password2"]
