# Generated by Django 4.0.3 on 2022-05-11 02:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0019_remove_abstask_previous_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='artifact_content_type',
        ),
        migrations.RemoveField(
            model_name='task',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='task',
            name='previous',
        ),
        migrations.RemoveField(
            model_name='task',
            name='process',
        ),
        migrations.DeleteModel(
            name='Process',
        ),
        migrations.DeleteModel(
            name='Task',
        ),
    ]
