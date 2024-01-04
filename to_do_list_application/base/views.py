from datetime import datetime,timedelta , date
from django.shortcuts import render, redirect 
from django import forms
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy
from django.db.models import Case, When, Value, IntegerField
import json
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth import get_user_model


from django.db.models import F, Value, IntegerField


# Imports for Reordering Feature
from django.views import View
from django.shortcuts import redirect
from django.db import transaction

from .models import Task
from .forms import TaskForm, PositionForm
from django.http import HttpResponse
from django.views import View
from .models import Task

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()

    def clean_reenter_password(self):
        enter_password = self.cleaned_data.get("enter_password")
        reenter_password = self.cleaned_data.get("reenter_password")
        if enter_password and reenter_password and  enter_password != reenter_password:
            raise forms.ValidationError(_("The two password fields didn't match."))
        # Example: Check if the password contains at least 8 characters
        if len(reenter_password) < 8:
            raise forms.ValidationError(_("Password should be at least 8 characters long."))

        # Example: Check if the password contains the user's username
        username = self.cleaned_data.get("username")
        if username and reenter_password and username.lower() in reenter_password.lower():
            raise forms.ValidationError(_("Password should not contain your username."))

        return reenter_password


class CustomLoginView(LoginView):
    template_name = 'base/login.html'
    fields = '__all__'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('tasks')


class RegisterPage(FormView):
    template_name = 'base/register.html'
    form_class = UserCreationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('tasks')

    def form_valid(self, form):
        user = form.save()
        if user is not None:
            login(self.request, user)
        return super(RegisterPage, self).form_valid(form)

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('tasks')
        return super(RegisterPage, self).get(*args, **kwargs)


class TaskList(LoginRequiredMixin, ListView):
    model = Task
    context_object_name = 'tasks'
    template_name = 'base/task_list.html' 
    def get_queryset(self):
        category_filter = self.request.GET.get('category', '')
        queryset = Task.objects.filter(user=self.request.user)

        if category_filter:
            queryset = queryset.filter(category=category_filter)

        
        queryset = queryset.annotate(
            days_until_due=F('due_date') - date.today()
        ).order_by(
            # Order by due date in ascending order (tasks due early first)
            'days_until_due',
            # Order by priority in ascending order (high priority first)
            'priority'
        )

        return queryset
    def task_list(request):
        user = request.user
        search_input = request.GET.get('search-area', '')
        category_filter = request.GET.get('category', '')
        priority_filter = request.GET.get('priority', '')

        print(f"User: {user}")
        print(f"Category Filter: {category_filter}")
        print(f"Priority Filter: {priority_filter}")


        print(f"Filtered Tasks: {tasks}")

        context = {
            'tasks': tasks,
            'search_input': search_input,
        }

        return render(request, 'your_app/task_list.html', context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks'] = context['tasks'].filter(user=self.request.user)
        context['count'] = context['tasks'].filter(complete=False).count()
        context['selected_category'] = self.request.GET.get('category', '') 
        search_input = self.request.GET.get('search-area') or ''
        if search_input:
            context['tasks'] = context['tasks'].filter(
                title__contains=search_input)

        context['search_input'] = search_input

        return context

class TaskDetail(LoginRequiredMixin, DetailView):
    model = Task
    context_object_name = 'task'
    template_name = 'base/task.html'


class TaskCreate(LoginRequiredMixin, CreateView):
    model = Task
    fields = ['title', 'description', 'complete','priority','due_date','category']
    success_url = reverse_lazy('tasks')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(TaskCreate, self).form_valid(form)


class TaskUpdate(LoginRequiredMixin, UpdateView):
    model = Task
    fields = ['title', 'description', 'complete','priority','due_date','category']
    success_url = reverse_lazy('tasks')
    def form_valid(self, form):
        # Retrieve the existing task
        existing_task = self.get_object()

        # Check if the due date has been changed
        new_due_date = form.cleaned_data.get('due_date')
        if new_due_date is not None and new_due_date != existing_task.due_date:
            # Due date has been changed, perform validation
            if new_due_date < date.today():
                form.add_error('due_date', 'Due date cannot be in the past.')
                return self.form_invalid(form)
        elif existing_task.due_date is None:
            # Handle the case where the existing due date is None
            pass
        else:
            # Due date hasn't been changed, use the existing due date
            form.instance.due_date = existing_task.due_date

        form.instance.user = self.request.user
        return super(TaskUpdate, self).form_valid(form)
    
class DeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    context_object_name = 'task'
    success_url = reverse_lazy('tasks')
    def get_queryset(self):
        owner = self.request.user
        return self.model.objects.filter(user=owner)

class TaskReorder(View):
    def post(self, request):
        form = PositionForm(request.POST)

        if form.is_valid():
            positionList = form.cleaned_data["position"].split(',')

            with transaction.atomic():
                self.request.user.set_task_order(positionList)

        return redirect(reverse_lazy('tasks'))
    
class ExportDataView(View):
    def get(self, request, *args, **kwargs):
        
        user_data = {
            'username': request.user.username,
            
        }
        tasks = Task.objects.filter(user=request.user)

       
        data = {
            'user_data': user_data,
            'tasks': [
                {
                    'title': task.title,
                    'description': task.description,
                    'complete': task.complete,
                    'category': task.category,
                    'priority': task.priority,
                    'due_date': task.due_date.isoformat() if task.due_date else None,
                }
                for task in tasks
            ],
        }

       
        response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="exported_data.json"'

        return response

        
