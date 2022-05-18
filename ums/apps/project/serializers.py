from rest_framework import serializers
from django.contrib.auth.models import Group
from django.conf import settings
from taggit.serializers import TaggitSerializer, TagListSerializerField
from ums.apps.accounts.serializers import UserSerializer
from .models import Project, Process, Task, FileManager, Achievement
from .utils import AchievementStateChoices
from .activation import STATUS


class FileManagerSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField()
    file_name = serializers.CharField(source='file.name', read_only=True)

    class Meta:
        model = FileManager
        fields = "__all__"

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret['file_name']:
            ret['file_name'] = ret['file_name'].split('/')[-1]

        return ret


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

    # project_sponsor = serializers.JSONField()

    class Meta:
        model = Achievement
        fields = "__all__"

    def get_state_display_name(self, instance):
        if instance.state == AchievementStateChoices.SUB:
            if instance.status1 == STATUS.DONE and instance.status2 != STATUS.DONE:
                return '已提交，等待分管领导审批。'
            else:
                return '已提交，等待负责人审批。'
        elif instance.state == AchievementStateChoices.APP:
            if instance.status1 == STATUS.DONE and instance.status2 != STATUS.DONE:
                return '负责人审核通过'
            if instance.status2 == STATUS.DONE:
                return '分管领导审核通过'
        elif instance.state == AchievementStateChoices.DENY:
            if instance.status1 == STATUS.ERROR:
                return '负责人驳回。'
            if instance.status2 == STATUS.ERROR:
                return '分管领导驳回'
        elif instance.state == AchievementStateChoices.WITHDRAW:
            return '已撤销'
        else:
            return '新创建'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['project_sponsor'] = [{'id': i.id, 'name': i.name} for i in instance.project.project_sponsor.all()]
        ret['project_approver'] = [{'id': i.id, 'name': i.name} for i in instance.project.project_approver.all()]
        ret['state_display_name'] = self.get_state_display_name(instance)
        return ret


class ArtifactObjectRelatedField(serializers.RelatedField):

    def to_representation(self, value):
        if isinstance(value, Achievement):
            serializer = AchievementSerializer(value)
        elif isinstance(value, Project):
            serializer = ProjectSerializer(value)
        else:
            raise Exception('Unexpected Type')
        return serializer.data


class ProcessSerializer(serializers.ModelSerializer):
    artifact = ArtifactObjectRelatedField(read_only=True)

    class Meta:
        model = Process
        fields = "__all__"


class TaskSerializer(serializers.ModelSerializer):
    artifact = ArtifactObjectRelatedField(read_only=True)

    class Meta:
        model = Task
        fields = "__all__"
