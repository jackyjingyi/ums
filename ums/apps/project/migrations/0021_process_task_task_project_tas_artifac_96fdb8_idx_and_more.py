# Generated by Django 4.0.3 on 2022-05-11 02:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
        ('project', '0020_remove_task_artifact_content_type_remove_task_owner_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Process',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(default='NEW', max_length=50, verbose_name='Status')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('finished', models.DateTimeField(blank=True, null=True, verbose_name='Finished')),
                ('artifact_object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('data', models.JSONField(blank=True, null=True)),
                ('artifact_content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.contenttype')),
            ],
            options={
                'verbose_name': 'Process',
                'verbose_name_plural': 'Process list',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flow_task_type', models.CharField(max_length=50, verbose_name='Type')),
                ('status', models.CharField(db_index=True, default='NEW', max_length=50, verbose_name='Status')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('assigned', models.DateTimeField(blank=True, null=True, verbose_name='Assigned')),
                ('started', models.DateTimeField(blank=True, null=True, verbose_name='Started')),
                ('finished', models.DateTimeField(blank=True, null=True, verbose_name='Finished')),
                ('artifact_object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('external_task_id', models.CharField(blank=True, db_index=True, max_length=50, null=True, verbose_name='External Task ID')),
                ('owner_permission', models.CharField(blank=True, max_length=255, null=True, verbose_name='Permission')),
                ('comments', models.TextField(blank=True, null=True, verbose_name='Comments')),
                ('data', models.JSONField(blank=True, null=True)),
                ('artifact_content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.contenttype')),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='project_task_owner', to=settings.AUTH_USER_MODEL, verbose_name='Owner')),
                ('previous', models.ManyToManyField(related_name='leading', to='project.task', verbose_name='Previous')),
                ('process', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.process', verbose_name='Process')),
            ],
            options={
                'verbose_name': 'Task',
                'verbose_name_plural': 'Tasks',
                'ordering': ['-created'],
            },
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['artifact_content_type', 'artifact_object_id'], name='project_tas_artifac_96fdb8_idx'),
        ),
        migrations.AddIndex(
            model_name='process',
            index=models.Index(fields=['artifact_content_type', 'artifact_object_id'], name='project_pro_artifac_be0981_idx'),
        ),
    ]