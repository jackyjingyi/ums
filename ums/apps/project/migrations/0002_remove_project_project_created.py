# Generated by Django 4.0.3 on 2022-04-24 10:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='project_created',
        ),
    ]
