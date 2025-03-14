from django import forms
from tempus_dominus.widgets import DateTimePicker
from .models import Event

from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start_time', 'end_time']
