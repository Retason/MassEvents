from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import BonusTask, QuizQuestion
from django.forms import modelformset_factory

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES[1:], required=True, label="Выберите роль")

    class Meta:
        model = User
        fields = ["username", "email", "role", "password1", "password2"]


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Имя пользователя",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )


class BonusTaskForm(forms.ModelForm):
    class Meta:
        model = BonusTask
        fields = ['name', 'description', 'type', 'code', 'reward', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'code': forms.TextInput(attrs={'placeholder': 'Кодовое слово'}),
            'reward': forms.NumberInput(attrs={'min': 1}),
        }

    def clean_code(self):
        task_type = self.cleaned_data.get('type')
        code = self.cleaned_data.get('code')
        if task_type == 'code' and not code:
            raise forms.ValidationError("Для задания с типом 'код' необходимо ввести код.")
        return code


QuizQuestionFormSet = modelformset_factory(
    QuizQuestion,
    fields=('question', 'correct_answer'),
    extra=3,
    widgets={'question': forms.Textarea(attrs={'rows': 2})}
)
