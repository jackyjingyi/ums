from rest_framework import serializers
from django.contrib.auth.models import Group
from django.conf import settings
from taggit.serializers import TaggitSerializer, TagListSerializerField
from ums.apps.accounts.serializers import UserSerializer
from .models import Project, Process, Task, FileManager, Achievement


class FileManagerSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField()

    class Meta:
        model = FileManager
        fields = "__all__"


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            'id',
            'project_id',
            'project_title',
            'project_type',
            'get_project_type_display',
            'project_cate',
            'get_project_cate_display',
            'project_members',
            'project_sponsor',
            'project_issuer',
            'project_approver',
            # 'project_created'
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['project_members'] = [{'id': i.id, 'name': i.name} for i in instance.project_members.all()]
        ret['project_sponsor'] = [{'id': i.id, 'name': i.name} for i in instance.project_sponsor.all()]
        ret['project_issuer'] = {'id': instance.project_issuer.id, 'name': instance.project_issuer.name}
        ret['project_approver'] = [{'id': i.id, 'name': i.name} for i in instance.project_approver.all()]
        return ret


class AchievementSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source='project.project_title', read_only=True)
    creator_name = serializers.CharField(source='creator.name', read_only=True)
    files = FileManagerSerializer(many=True, read_only=True)

    class Meta:
        model = Achievement
        fields = "__all__"


class ProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Process
        fields = "__all__"


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"
