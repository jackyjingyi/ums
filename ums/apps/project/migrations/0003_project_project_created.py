# Generated by Django 4.0.3 on 2022-04-24 10:45

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0002_remove_project_project_created'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='project_created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='项目创建时间'),
            preserve_default=False,
        ),
    ]
