from django import forms
from .models import Task
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.forms.widgets import DateInput
from datetime import date
class PositionForm(forms.Form):
    position = forms.CharField()

class TaskForm(forms.ModelForm):
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, initial='medium')

    class Meta:
        model = Task
        fields = ['title', 'description', 'complete', 'priority', 'due_date']
        widgets = {
            'due_date': DateInput(attrs={'type': 'date'}),
        }

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')

        if due_date and due_date < date.today():
            raise forms.ValidationError("Due date cannot be from the past.")

        return due_date

    



