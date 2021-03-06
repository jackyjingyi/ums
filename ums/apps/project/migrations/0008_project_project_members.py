# Generated by Django 4.0.3 on 2022-05-05 01:42

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('project', '0007_remove_project_project_team'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='project_members',
            field=models.ManyToManyField(db_index=True, limit_choices_to={'role__exclude': 4}, related_name='member', related_query_name='project_member', to=settings.AUTH_USER_MODEL, verbose_name='项目组成员'),
        ),
    ]
