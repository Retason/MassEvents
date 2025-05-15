from django import forms
from django.utils.timezone import is_naive, make_aware, now
from .models import Event, EventStage, EventTask
from datetime import datetime


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'location', 'start_time', 'end_time',
            'max_participants', 'image', 'registration_closed', 'enable_tasks'
        ]
        widgets = {
            'start_time': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_start_time'}),
            'end_time': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_end_time'}),
        }

    def clean_start_time(self):
        start_time = self.cleaned_data.get('start_time')

        if isinstance(start_time, str):
            try:
                return datetime.strptime(start_time, "%d.%m.%Y, %H:%M")
            except ValueError:
                raise forms.ValidationError("Введите дату в формате ДД.ММ.ГГГГ, ЧЧ:ММ.")

        return start_time

    def clean_end_time(self):
        end_time = self.cleaned_data.get('end_time')

        if isinstance(end_time, str):
            try:
                return datetime.strptime(end_time, "%d.%m.%Y, %H:%M")
            except ValueError:
                raise forms.ValidationError("Введите дату в формате ДД.ММ.ГГГГ, ЧЧ:ММ.")

        return end_time


class EventStageForm(forms.ModelForm):
    class Meta:
        model = EventStage
        fields = ['title', 'description', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_start_time'}),
            'end_time': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_end_time'}),
        }


class EventTaskForm(forms.ModelForm):
    class Meta:
        model = EventTask
        fields = ['title', 'description', 'type', 'code', 'reward', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'code': forms.TextInput(attrs={'placeholder': 'Кодовое слово или правильный ответ'}),
            'reward': forms.NumberInput(attrs={'min': 1}),
            'type': forms.Select(attrs={'class': 'input'}),
        }

    def clean_code(self):
        task_type = self.cleaned_data.get('type')
        code = self.cleaned_data.get('code')
        if task_type in ['code', 'question'] and not code:
            raise forms.ValidationError("Необходимо указать код или ответ.")
        return code
