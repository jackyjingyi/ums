# Generated by Django 4.0.3 on 2022-05-17 01:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0021_process_task_task_project_tas_artifac_96fdb8_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='achievement',
            name='state',
            field=models.CharField(choices=[('1', '新创建'), ('2', '已提交'), ('3', '审批通过'), ('4', '审批驳回'), ('5', '已撤销')], db_index=True, default='1', max_length=5, verbose_name='流程状态'),
        ),
        migrations.AlterField(
            model_name='achievement',
            name='status1',
            field=models.CharField(default='NEW', max_length=25, verbose_name='一级审批状态'),
        ),
        migrations.AlterField(
            model_name='achievement',
            name='status2',
            field=models.CharField(default='NEW', max_length=25, verbose_name='二级审批状态'),
        ),
    ]