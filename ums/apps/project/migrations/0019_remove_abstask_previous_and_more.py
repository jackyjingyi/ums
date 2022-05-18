# Generated by Django 4.0.3 on 2022-05-11 02:17

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0018_process_project_pro_artifac_be0981_idx'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='abstask',
            name='previous',
        ),
        migrations.RemoveField(
            model_name='process',
            name='absprocess_ptr',
        ),
        migrations.RemoveField(
            model_name='task',
            name='abstask_ptr',
        ),
        migrations.AddField(
            model_name='process',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Created'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='process',
            name='finished',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Finished'),
        ),
        migrations.AddField(
            model_name='process',
            name='id',
            field=models.BigAutoField(auto_created=True, default=1, primary_key=True, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='process',
            name='status',
            field=models.CharField(default='NEW', max_length=50, verbose_name='Status'),
        ),
        migrations.AddField(
            model_name='task',
            name='assigned',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Assigned'),
        ),
        migrations.AddField(
            model_name='task',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Created'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='task',
            name='finished',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Finished'),
        ),
        migrations.AddField(
            model_name='task',
            name='flow_task_type',
            field=models.CharField(default='SINGLE', max_length=50, verbose_name='Type'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='task',
            name='id',
            field=models.BigAutoField(auto_created=True, default=1, primary_key=True, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='task',
            name='previous',
            field=models.ManyToManyField(related_name='leading', to='project.task', verbose_name='Previous'),
        ),
        migrations.AddField(
            model_name='task',
            name='started',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Started'),
        ),
        migrations.AddField(
            model_name='task',
            name='status',
            field=models.CharField(db_index=True, default='NEW', max_length=50, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='achievement',
            name='state',
            field=models.CharField(choices=[('1', '新创建'), ('2', '已提交'), ('3', '一级审批通过'), ('4', '一级审批驳回'), ('5', '已撤销')], db_index=True, default='1', max_length=5, verbose_name='流程状态'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['artifact_content_type', 'artifact_object_id'], name='project_tas_artifac_96fdb8_idx'),
        ),
        migrations.DeleteModel(
            name='AbsProcess',
        ),
        migrations.DeleteModel(
            name='AbsTask',
        ),
    ]
