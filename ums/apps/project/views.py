import json
import logging
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from guardian.shortcuts import assign_perm, get_users_with_perms
from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, permission_classes
from rest_framework.decorators import action
from rest_framework.permissions import DjangoObjectPermissions, DjangoModelPermissions, \
    DjangoModelPermissionsOrAnonReadOnly
from rest_framework import viewsets
from rest_framework import status
from .models import Project, Process, Task, FileManager, Achievement
from .serializers import ProjectSerializer, ProcessSerializer, TaskSerializer, FileManagerSerializer, \
    AchievementSerializer
from ..accounts.utils import RoleChoices
from .utils import ProjectStatusChoices

__all__ = (
    'ProcessCreateListView',
    'ProcessDetailView',
    'TaskListCreateView',
    'TaskDetailView',
    'ProjectViewSet',
    'AchievementViewSet',
    'FileManagerViewSet'
)
User = get_user_model()


class SmallResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    page_query_param = "page"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'current': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'results': data,
        })


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    pagination_class = SmallResultsSetPagination
    # 秘书、管理员可以创建、修改、删除，其他用户可以查看
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def perform_create(self, serializer):
        instance = serializer.save()
        # add permissions to project members
        # step1. members exists
        members = instance.project_members
        if members.count() > 0:
            # assign view project permissions to all members
            for user in members.all():
                # assign view project permission to associated user
                # todo: may change to all user
                assign_perm('view_project', user, instance)
                # assign add achievement permission to user
                # todo: may change to all users
                assign_perm('project.add_achievement', user)
                assign_perm('project.add_filemanager', user)
        else:
            logging.error('Project-Creation: need select project Members')

    @action(detail=False, )
    def get_my_projects(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied()
        queryset = request.user.member.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AchievementViewSet(viewsets.ModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    pagination_class = SmallResultsSetPagination

    @permission_classes([DjangoModelPermissionsOrAnonReadOnly])
    def create(self, request, *args, **kwargs):
        # todo: check project status; if finished => no achievement allow to be created
        # todo: write a decorator
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.validated_data.get('project')

        if project.status != ProjectStatusChoices.NEW.value and project.status != ProjectStatusChoices.START.value:
            return Response({'msg': '项目已完结或锁定，无法创建成果，请于管理员联系。'}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @permission_classes([DjangoObjectPermissions])
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        print(request.data)
        print(partial, 'is partial')
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_create(self, serializer):
        instance = serializer.save()
        # assign perm
        try:
            # step1. assign change_achievement, delete_achievement, view_achievement to achievement creator
            assert instance.creator == self.request.user.id

            assign_perm('change_achievement', instance.creator, instance)
            assign_perm('submit_achievement', instance.creator, instance)
            assign_perm('delete_achievement', instance.creator, instance)
            # todo: submit_achievement;
            # step2. all project members should have view achievement permission(maybe to all users)
            project = instance.project  # Project object
            members = project.project_members
            for member in members:
                assign_perm('view_achievement', member, instance)

            sponsors = project.project_sponsor  # m2m manager
            # todo: lv1_approval
            assert sponsors.count() > 0
            for sponsor in sponsors:
                assign_perm('approve_achievement_lv1', sponsor, instance)
            # step3. project leader permissions
            leaders = project.project_approver
            assert leaders.count() > 0
            for leader in leaders:
                assign_perm('approve_achievement_lv2', leader, instance)
            secretaries = User.objects.filter(
                role__in=(RoleChoices.SECRETARY.value, RoleChoices.ADMIN.value, RoleChoices.DEV.value))
            assert secretaries.count() > 0
            for secretary in secretaries:
                assign_perm('final_review_achievement', secretary, instance)
        except AssertionError:
            # only write to log system.
            logging.error(
                f"""{instance.id} permission assignment not finish! May caused by no leader or sponsor provided by project instance.""")

    @action(detail=True)
    @permission_classes([DjangoObjectPermissions])
    def submit(self, request, *args, **kwargs):
        """
        submit method， change status to submit
        :param request:
        :return:
        """

        instance = self.get_object()
        if not request.user.has_perm('submit_achievement', instance):
            raise PermissionDenied()
        serializer = self.get_serializer(instance)
        # call process handler
        # processhandler(instance)

        return Response(serializer.data)


    def perform_submit(self):
        """
        permission upadte
        :return:
        """
        pass

    @action(detail=True)
    def withdraw(self, request):
        """

        :param request:
        :return:
        """
        pass

    def perform_withdraw(self):
        """

        :return:
        """
        pass

    @action(detail=True)
    def review(self, request):
        """
        secretary review
        :param request:
        :return:
        """
        pass

    def perform_review(self):
        pass

    @action(detail=True)
    def update_status(self, request):
        """
        待定
        :param request:
        :return:
        """
        pass

    def perform_update_status(self):
        pass

    @action(detail=False)
    def get_achievements_by_projectid(self, request):
        # l = Achievement.objects.filter(project_id=request.query_params.get('projectid'))
        queryset = self.filter_queryset(self.get_queryset()).filter(project_id=request.query_params.get('projectid'))
        print(queryset, request.query_params.get('projectid'))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def get_request_user_permissions(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            if request.query_params.get('user_id'):
                user = User.objects.get(pk=request.query_params.get('user_id'))
            else:
                raise PermissionDenied()
        instance = self.get_object()
        # contains object permissions against this achievement
        permissions = get_users_with_perms(instance, attach_perms=True, with_superusers=False)
        # filter permissions
        data = []
        if permissions.get(user):
            data = permissions.get(user)

        return Response(data)


class FileManagerViewSet(viewsets.ModelViewSet):
    queryset = FileManager.objects.all()
    serializer_class = FileManagerSerializer
    pagination_class = SmallResultsSetPagination

    def create(self, request, *args, **kwargs):
        print(request.user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """
        1. 用户是为项目组成员，否返回403；
        2. or 用户是ADMIN/DEV，否返回403；
        3. 新创建的instance无需关注是否取消删除权限等；
        :param serializer:
        :return:
        """
        if self.request.user.is_authenticated:
            # check if user id in project team
            achievement = serializer.validated_data.get('achievement')

            if self.request.user in achievement.project.project_members.all():
                logging.info("Current user in project team!")
            elif self.request.user.role == RoleChoices.ADMIN.value or self.request.user.role == RoleChoices.DEV.value:
                logging.info("Admin user or Developer creating file!")
            else:
                logging.warning("request user is not in project members!")
                raise PermissionDenied()
            instance = serializer.save()
            logging.warning(
                f"""Bind file {instance.id} to {self.request.user.name}, user role is {self.request.user.get_role_display()}""")
            # 检查是否具有delete权限
            logging.info(
                f"""{self.request.user.name} has perm {'delete_filemanager'} : {self.request.user.has_perm('delete_filemanager', instance)}""")
            # assign_perm()
        else:
            raise PermissionDenied()



    @action(detail=False)
    def get_latest_tags(self, request):
        # return latest 10 tags
        tag_set = set()
        for obj in self.queryset.order_by('-created'):
            if len(tag_set) >= 10:
                break
            else:
                if obj.tags.count() > 0:
                    for n in obj.tags.names():
                        tag_set.add(n)
        res = []
        if tag_set:
            for i in tag_set:
                res.append(
                    {'label': i, 'value': i}
                )
        return Response(res)

    @action(detail=False)
    def get_files_by_achievement_id(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        if request.query_params.get('achievement_id'):
            try:
                queryset = queryset.filter(achievement=request.query_params.get('achievement_id'))
            except:
                return Response({'msg': '请求错误。'}, status=status.HTTP_400_BAD_REQUEST)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProcessCreateListView(generics.ListCreateAPIView):
    queryset = Process.objects.all()
    serializer_class = ProcessSerializer


class ProcessDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Process.objects.all()
    serializer_class = ProcessSerializer


class TaskListCreateView(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class TaskDetailView(generics.RetrieveUpdateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
