from django import forms
from datetime import datetime
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'text'}
            ),
            'end_time': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'text'}
            ),
        }

    def clean_start_time(self):
        """Принудительно парсим дату, чтобы Django её принял"""
        start_time = self.cleaned_data.get('start_time')

        if isinstance(start_time, str):
            try:
                return datetime.strptime(start_time, "%d.%m.%Y, %H:%M")
            except ValueError:
                raise forms.ValidationError("Введите дату в формате ДД.ММ.ГГГГ, ЧЧ:ММ.")

        return start_time

    def clean_end_time(self):
        """Принудительно парсим дату, чтобы Django её принял"""
        end_time = self.cleaned_data.get('end_time')

        if isinstance(end_time, str):
            try:
                return datetime.strptime(end_time, "%d.%m.%Y, %H:%M")
            except ValueError:
                raise forms.ValidationError("Введите дату в формате ДД.ММ.ГГГГ, ЧЧ:ММ.")

        return end_time
