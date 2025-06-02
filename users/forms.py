from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import BonusTask, QuizQuestion, Comment, Ticket, OrganizerApplication, TicketMessage
from django.forms import modelformset_factory

ALLOWED_DOMAINS = {
    'gmail.com', 'yandex.ru', 'mail.ru', 'outlook.com', 'icloud.com',
    'protonmail.com', 'rambler.ru', 'bk.ru', 'inbox.ru', 'list.ru', 'mpt.ru'
}

User = get_user_model()


class RegisterForm(UserCreationForm):
    def clean_email(self):
        email = self.cleaned_data['email']
        domain = email.split('@')[-1].lower()

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


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Добавьте комментарий...', 'class': 'form-control'})
        }


class TicketForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_types = ['question', 'report']
        self.fields['type'].choices = [c for c in self.fields['type'].choices if c[0] in allowed_types]

    class Meta:
        model = Ticket
        fields = ['type', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }


class ReportCommentForm(forms.Form):
    reason = forms.CharField(
        label="Причина жалобы",
        widget=forms.Textarea(attrs={
            'class': 'input',
            'placeholder': 'Опишите причину жалобы',
            'rows': 4
        })
    )


class OrganizerApplicationForm(forms.ModelForm):
    class Meta:
        model = OrganizerApplication
        fields = ['passport_series', 'passport_number', 'issued_by', 'date_issued']
        widgets = {
            'date_issued': forms.DateInput(attrs={'type': 'date'})
        }


class TicketMessageForm(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Введите сообщение...',
                'class': 'input'
            })
        }