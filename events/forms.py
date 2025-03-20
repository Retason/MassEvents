from django import forms
from django.utils.timezone import is_naive, make_aware, now
from .models import Event, EventStage
from datetime import datetime


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start_time', 'end_time', 'max_participants', 'image', 'registration_closed']
        widgets = {
            'start_time': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_start_time'}),
            'end_time': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_end_time'}),
        }

    def clean_start_time(self):
        """Обрабатываем дату начала"""
        start_time = self.cleaned_data.get('start_time')

        if isinstance(start_time, str):
            try:
                return datetime.strptime(start_time, "%d.%m.%Y, %H:%M")
            except ValueError:
                raise forms.ValidationError("Введите дату в формате ДД.ММ.ГГГГ, ЧЧ:ММ.")

        return start_time

    def clean_end_time(self):
        """Обрабатываем дату окончания"""
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
