from rest_framework import serializers
from django.contrib.auth.models import Group
from django.conf import settings
from taggit.serializers import TaggitSerializer, TagListSerializerField
from ums.apps.accounts.serializers import UserSerializer
from .models import Project, Process, Task, FileManager, Achievement
from .utils import AchievementStateChoices
from .activation import STATUS, STATUS_DISPLAY


def get_status_display(status):
    return STATUS_DISPLAY[status]


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
        ret.pop('file')
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
            if instance.status1 == STATUS.DENY:
                return '负责人驳回。'
            if instance.status2 == STATUS.DENY:
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


class TaskSerializer(serializers.ModelSerializer):
    project_id = serializers.CharField(source='artifact.project.id')
    project_name = serializers.CharField(source='artifact.project.project_title')
    achievement_name = serializers.CharField(source='artifact.name')

    class Meta:
        model = Task
        fields = "__all__"
        ordering = ['finished', 'id']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance:
            ret['owner_name'] = instance.owner.name
            ret['owner_mime'] = instance.owner.mime
            ret['status_display'] = get_status_display(instance.status)
            ret['submitted_by'] = instance.data.get('submitted_by', 'person')
        return ret


class ProcessSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True, many=True)

    class Meta:
        model = Process
        fields = "__all__"
        ordering = ['finished']
