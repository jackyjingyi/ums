# Generated by Django 4.0.3 on 2022-05-10 03:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('project', '0016_alter_achievement_options_alter_project_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='achievement',
            name='is_finished',
            field=models.BooleanField(db_index=True, default=False, help_text='流程走完，需要商务秘书及时review'),
        ),
        migrations.AddField(
            model_name='achievement',
            name='is_reviewed',
            field=models.BooleanField(db_index=True, default=False, help_text='对接展示'),
        ),
        migrations.AddField(
            model_name='achievement',
            name='state',
            field=models.CharField(choices=[('1', '新创建')], db_index=True, default='1', max_length=5, verbose_name='流程状态'),
        ),
        migrations.AddField(
            model_name='achievement',
            name='status1',
            field=models.CharField(default='NEW', max_length=5, verbose_name='一级审批状态'),
        ),
        migrations.AddField(
            model_name='achievement',
            name='status2',
            field=models.CharField(default='NEW', max_length=5, verbose_name='二级审批状态'),
        ),
        migrations.AlterField(
            model_name='achievement',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='achievement_creator', to=settings.AUTH_USER_MODEL),
        ),
    ]