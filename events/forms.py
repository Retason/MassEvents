from django import forms
from datetime import datetime
from .models import Event, EventStage

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_start_time'}),
            'end_time': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_end_time'}),
        }

    def clean_end_time(self):
        """Принудительно парсим дату, чтобы Django её принял"""
        end_time = self.cleaned_data.get('end_time')

        if not end_time:
            raise forms.ValidationError("Дата окончания мероприятия обязательна.")

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