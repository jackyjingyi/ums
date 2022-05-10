import json
from django.db.models.query import QuerySet
from django.conf import settings
from django.contrib.auth.models import Permission

from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from guardian.shortcuts import assign_perm
from .models import OCTUser, GroupType, GroupProfile
from .serializers import UserSerializer, GroupTypeSerializer, GroupProfileSerializer
from .utils import RoleChoices

__all__ = ['GroupTypeListView', 'GroupTypeDetailView', 'GroupProfileListView', 'UserViewSet']


class UserViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for listing or retrieving users.
    """
    queryset = OCTUser.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'phone_number'
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        try:
            other_param = self.request.query_params.dict()
            if "format" in other_param.keys():
                other_param.pop("format")
        except json.decoder.JSONDecodeError:
            other_param = None
        queryset = self.queryset

        if isinstance(queryset, QuerySet):
            if other_param:
                queryset = queryset.filter(**other_param)
            else:
                queryset = queryset.all()
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        instance = serializer.save()
        # 增加秘书权限
        if instance.role == RoleChoices.SECRETARY.value or instance.role == RoleChoices.ADMIN.value or instance.role == RoleChoices.DEV.value:
            permissions = (
                'project.add_project', 'project.change_project', 'project.view_project', 'project.delete_project'
            )
            for p in permissions:
                assign_perm(p, instance)


    @action(detail=False)
    def get_sponsor_users(self, request):
        # todo add try catch
        sponsors = OCTUser.objects.filter(role=RoleChoices.PROJECT_SPONSOR.value)
        data = []
        for obj in sponsors:
            if obj:
                data.append({
                    'value': obj.id,
                    'label': obj.name,
                })
        return Response(data)

    @action(detail=False)
    def get_approver_users(self, request):
        # todo add try catch
        sponsors = OCTUser.objects.filter(role=RoleChoices.APPROVAL_LEADER.value)
        data = []
        for obj in sponsors:
            if obj:
                data.append({
                    'value': obj.id,
                    'label': obj.name,
                })
        return Response(data)

    @action(detail=False)
    def get_member_users(self, request):
        # todo add try catch
        sponsors = OCTUser.objects.filter(role__in=[RoleChoices.PROJECT_SPONSOR.value, RoleChoices.PROJECT_WORKER.value,
                                                    RoleChoices.SECRETARY.value, RoleChoices.ADMIN.value])
        data = []
        for obj in sponsors:
            if obj:
                data.append({
                    'value': obj.id,
                    'label': f"""{str(obj.name)}""",
                })
        return Response(data)


class GroupTypeListView(generics.ListAPIView):
    # permission_classes = (IsAuthenticated,)
    queryset = GroupType.objects.all()
    serializer_class = GroupTypeSerializer


class GroupTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    # permission_classes = (IsAuthenticated,)
    serializer_class = GroupTypeSerializer
    queryset = GroupType.objects.all()
    # lookup_field = 'type'


class GroupProfileListView(generics.ListAPIView):
    serializer_class = GroupProfileSerializer
    queryset = GroupProfile.objects.all()
