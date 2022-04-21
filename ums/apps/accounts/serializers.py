from django.contrib.auth.models import Group
from rest_framework import serializers
from .models import OCTUser, GroupType, GroupProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = OCTUser
        fields = ('id', 'name', 'phone_number', 'role', 'mime', 'groups', 'user_permissions', 'department', 'username')
        depth = 1


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"


class GroupTypeSerializer(serializers.ModelSerializer):
    group = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = GroupType
        fields = "__all__"
        depth = 1


class GroupProfileSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)
    supervisor = UserSerializer(read_only=True)
    leader = UserSerializer(read_only=True, many=True)

    class Meta:
        model = GroupProfile
        fields = "__all__"
        # depth = 1
