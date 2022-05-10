# Generated by Django 4.0.3 on 2022-05-06 03:55

from django.db import migrations, models
import django.db.models.deletion
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0005_auto_20220424_2025'),
        ('project', '0013_filemanager_tags'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaggedFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='filemanager',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='project.TaggedFile', to='taggit.Tag', verbose_name='标签'),
        ),
        migrations.AddField(
            model_name='taggedfile',
            name='content_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.filemanager'),
        ),
        migrations.AddField(
            model_name='taggedfile',
            name='tag',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s_items', to='taggit.tag'),
        ),
    ]