# Generated by Django 4.0.3 on 2022-05-05 01:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0006_achievement_created_achievement_updated'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='project_team',
        ),
    ]
