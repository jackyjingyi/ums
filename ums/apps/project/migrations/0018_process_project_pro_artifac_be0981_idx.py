# Generated by Django 4.0.3 on 2022-05-10 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0017_achievement_is_finished_achievement_is_reviewed_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='process',
            index=models.Index(fields=['artifact_content_type', 'artifact_object_id'], name='project_pro_artifac_be0981_idx'),
        ),
    ]
