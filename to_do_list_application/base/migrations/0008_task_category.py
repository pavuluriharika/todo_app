# Generated by Django 4.1.7 on 2023-12-05 11:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0007_task_due_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='category',
            field=models.CharField(default='DefaultCategory', max_length=100),
        ),
    ]
