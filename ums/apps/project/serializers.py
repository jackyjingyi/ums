from rest_framework import serializers
from django.contrib.auth.models import Group
from django.conf import settings
from .models import Project, Process, Task, FileManager



class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = (
            'project_id',
            'project_title',
            'project_type',
            'get_project_type_display',
            'project_cate',
            'get_project_cate_display',
            'project_team',
            'project_sponsor',
            'project_issuer',
            'project_approver',
        )


    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['project_team'] = [{'id':i.id,'name':i.name} for i in instance.project_team.all()]
        ret['project_sponsor'] = [{'id':i.id,'name':i.name} for i in instance.project_sponsor.all()]
        ret['project_issuer'] = {'id':instance.project_issuer.id,'name':instance.project_issuer.name}
        ret['project_approver'] = [{'id':i.id,'name':i.name} for i in instance.project_approver.all()]
        return ret

class ProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Process
        fields = "__all__"


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"


class FileManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileManager
        fields = "__all__"
