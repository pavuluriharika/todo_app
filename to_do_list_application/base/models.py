from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
# Create your models here.
class Task(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    complete = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True) 
    category = models.CharField(max_length=255, choices=[('work', 'Work'), ('personal', 'Personal'), ('other', 'Other')])
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    def __str__(self):
        return self.title
    def save(self, *args, **kwargs):
        if self.due_date is not None and self.due_date < date.today():
            # Set the due date to None if it's in the past
            #self.due_date = None
            raise ValidationError(_('Due date cannot be in the past'))

        super(Task, self).save(*args, **kwargs)

    class Meta:
        order_with_respect_to = 'user'

