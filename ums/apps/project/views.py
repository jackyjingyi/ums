import json
import logging
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from guardian.shortcuts import assign_perm, get_users_with_perms, get_user_perms, remove_perm, get_perms
from guardian.core import ObjectPermissionChecker
from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, permission_classes
from rest_framework.decorators import action
from rest_framework.reverse import reverse
from rest_framework.permissions import DjangoObjectPermissions, DjangoModelPermissions, \
    DjangoModelPermissionsOrAnonReadOnly, IsAuthenticated
from rest_framework import viewsets
from rest_framework import status
from .models import Project, Process, Task, FileManager, Achievement
from .serializers import ProjectSerializer, ProcessSerializer, TaskSerializer, FileManagerSerializer, \
    AchievementSerializer
from ..accounts.utils import RoleChoices
from .utils import ProjectStatusChoices, AchievementStateChoices
from .flow import AchievementProcessHandlerFirstStage, ActionHandler
from .activation import STATUS

__all__ = (
    'ProjectViewSet',
    'AchievementViewSet',
    'FileManagerViewSet',
    'ProcessViewSet',
    'TaskViewSet'

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
    # ???????????????????????????????????????????????????????????????????????????
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
            return Response({'msg': '????????????????????????????????????????????????????????????????????????'}, status=status.HTTP_400_BAD_REQUEST)
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
            assert instance.creator == self.request.user

            assign_perm('change_achievement', instance.creator, instance)
            assign_perm('submit_achievement', instance.creator, instance)
            assign_perm('delete_achievement', instance.creator, instance)
            # todo: submit_achievement;
            # step2. all project members should have view achievement permission(maybe to all users)
            project = instance.project  # Project object
            members = project.project_members
            for member in members.all():
                assign_perm('view_achievement', member, instance)

            secretaries = User.objects.filter(
                role__in=(RoleChoices.SECRETARY.value, RoleChoices.ADMIN.value, RoleChoices.DEV.value))
            assert secretaries.count() > 0
            for secretary in secretaries.all():
                assign_perm('final_review_achievement', secretary, instance)
        except AssertionError:
            # only write to log system.
            logging.error(
                f"""{instance.id} permission assignment not finish! May caused by no leader or sponsor provided by project instance.""")

    def check_process_exists(self, instance, lv):
        content_type_object = ContentType.objects.get(app_label=instance._meta.app_label,
                                                      model=instance._meta.model.__name__)
        if Process.objects.filter(~Q(status__in=[STATUS.DONE, STATUS.ERROR, STATUS.CANCELED, STATUS.DENY]),  # ????????????????????????
                                  data__activation='approval', artifact_content_type=content_type_object,
                                  artifact_object_id=instance.pk, data__stage=lv
                                  ).exists():
            # ??????????????????????????????????????????
            logging.critical('Process already exists!')
            return True
        return False

    @action(detail=True, methods=['put'])
    @permission_classes([DjangoObjectPermissions])
    def submit(self, request, *args, **kwargs):
        """
        first submit
        submit method??? change status to submit
        :param request:
        :return:
        """
        instance = self.get_object()
        stage = request.data.get('level', 1)
        data = {'state': AchievementStateChoices.SUB.value}
        print(request.data, kwargs, args)
        if request.data.get('level', 1) == 1 and request.user not in instance.project.project_sponsor.all():
            # lv1 approval process
            if self.check_process_exists(instance, 1):
                return Response({'msg': '????????????????????????????????????!'}, status=400)
            data['status1'] = STATUS.STARTED
        else:
            # ??????stage ==1 ?????????????????????????????????????????????????????????????????????
            # lv2 approval process
            try:
                if instance.status1 != STATUS.DONE:  # ????????????????????????
                    assert request.user in instance.project.project_sponsor.all()
                    # ??????????????????????????????
                    data['status1'] = STATUS.DONE
            except AssertionError:
                return Response({'msg': '???????????????????????????????????????!'}, status=400)
            if self.check_process_exists(instance, 2):
                return Response({'msg': '????????????????????????????????????!'}, status=400)
            stage = 2
            data['status2'] = STATUS.STARTED
        # ?????????????????????????????????process
        # ['change_achievement', 'delete_achievement', 'submit_achievement', 'view_achievement']
        logging.info(f'user permissions are {get_user_perms(request.user, instance)}')
        if not request.user.has_perm('submit_achievement', instance):
            # ???????????????????????????
            logging.warning(
                f"{request.user.name} doest has submit permisson against {instance}"
            )
            logging.warning(f'user permissions are {get_user_perms(request.user, instance)}')
            raise PermissionDenied()
        # when achievement creator is sponsor
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_submit(serializer, stage)
        return Response(serializer.data)

    def perform_submit(self, serializer, stage):
        user = self.request.user
        instance = serializer.save()
        perm = 'approve_achievement_lv1'
        if stage == 2:
            perm = 'approve_achievement_lv2'
        # ??????????????????????????? ???????????????????????????????????????????????????????????????, ??????????????????????????????
        uid = self.request.data.get('required_approver')
        try:
            approver = User.objects.filter(pk__in=[u.get('id') for u in uid])
            print(approver, instance.project.project_approver.all())
            for a in approver:
                print(a)
                if stage == 1:
                    assert a in instance.project.project_sponsor.all()

                else:
                    assert a in instance.project.project_approver.all()
                    assert instance.status1 == STATUS.DONE
                assign_perm(perm, a, instance)
        except AssertionError:
            raise Exception('Error')
        except:
            raise Exception('Error')

        remove_perm('submit_achievement', user, instance)
        remove_perm('delete_achievement', user, instance)
        remove_perm('change_achievement', user, instance)
        #
        assign_perm('withdraw_achievement', user, instance)
        data = self.request.data
        data['user'] = user
        AchievementProcessHandlerFirstStage.create_process(
            instance=instance,
            **data
        )
        logging.warning(f'after user permissions are {get_user_perms(self.request.user, instance)}')

    @action(detail=True, methods=['put'])
    @permission_classes([IsAuthenticated])
    def withdraw(self, request, *args, **kwargs):
        """
        ????????? ?????????????????????

        :param request:
        :return:
        """
        instance = self.get_object()
        user = request.user
        checker = ObjectPermissionChecker(user)
        print(request.data)
        if checker.has_perm('withdraw_achievement', instance):
            # ?????????????????????
            # step 1: add task withdraw
            # step 2: process => cancel
            withdraw_handler = ActionHandler(instance)
            withdraw_handler.withdraw(comments=request.data.get('comments', ''))
            remove_perm('withdraw_achievement', user, instance)
            assign_perm('submit_achievement', user, instance)
            assign_perm('change_achievement', user, instance)
            assign_perm('delete_achievement', user, instance)
            # remove approval permissions from sponsor and leaders
            for a in instance.project.project_sponsor.all():
                if 'approve_achievement_lv1' in get_perms(a, instance):
                    remove_perm('approve_achievement_lv1', a, instance)
            for a in instance.project.project_approver.all():
                if 'approve_achievement_lv2' in get_perms(a, instance):
                    remove_perm('approve_achievement_lv2', a, instance)
        else:
            raise PermissionDenied()
        # ????????? ?????????new???new
        data = {'state': AchievementStateChoices.WITHDRAW.value, 'status1': STATUS.NEW, 'status2': STATUS.NEW}
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

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

    @action(detail=True, methods=['put'])
    @permission_classes([IsAuthenticated])
    def approve(self, request, *args, **kwargs):
        # 1. ????????????
        # 2. ??????=???
        instance = self.get_object()
        user = request.user
        checker = ObjectPermissionChecker(user)
        print("approve task")
        print(request.data)
        print(request.data.get('comments', ''))
        if checker.has_perm('approve_achievement_lv1', instance) or checker.has_perm('approve_achievement_lv2',
                                                                                     instance):
            # ?????????1?????????2?????????

            # ?????????????????????????????????task??????instance??????object??????????????????
            # ?????????????????????????????????????????????????????????get
            approval_handler = ActionHandler(instance)
            process = approval_handler.approve(request.data.get('comments', ''), user)
            # ?????????=>?????????1?????????=>
        else:
            print('no permission')
            raise PermissionDenied()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods={'put'})
    @permission_classes([IsAuthenticated])
    def deny(self, request, *args, **kwargs):
        # achievement
        instance = self.get_object()
        # ?????????
        user = request.user
        checker = ObjectPermissionChecker(user)
        logging.info('Start deny Achievement. Perms are\r')
        logging.warning(get_perms(user, instance))
        if checker.has_perm('approve_achievement_lv1', instance) or checker.has_perm('approve_achievement_lv2',
                                                                                     instance):
            deny_handler = ActionHandler(instance)
            process = deny_handler.deny(request.data.get('comments', ''), user)
        else:
            print('no permission')
            raise PermissionDenied()
        logging.warning(get_perms(user, instance))
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False)
    def get_achievements_by_projectid(self, request):
        # l = Achievement.objects.filter(project_id=request.query_params.get('projectid'))
        queryset = self.filter_queryset(self.get_queryset()).filter(project_id=request.query_params.get('projectid'))

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
        permissions = get_user_perms(user, instance)

        return Response(permissions)


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
        1. ???????????????????????????????????????403???
        2. or ?????????ADMIN/DEV????????????403???
        3. ????????????instance??????????????????????????????????????????
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
            # ??????????????????delete??????
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
                return Response({'msg': '???????????????'}, status=status.HTTP_400_BAD_REQUEST)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True)
    @permission_classes([IsAuthenticated])
    def get_file_url(self, request, *args, **kwargs):
        instance = self.get_object()
        # user should have change_achievement or approve_achievement permissions
        achievement = instance.achievement
        user = request.user
        checker = ObjectPermissionChecker(user)
        if not self._download_permission_check(user, checker, achievement):
            raise PermissionDenied()

        return Response(
            {'id': instance.pk, 'file_url': f'{request.scheme}://{request.get_host()}{instance.file.url}'}, status=200
        )

    def _download_permission_check(self, user, checker, achievement):
        if checker.has_perm('approve_achievement_lv1', achievement) or checker.has_perm('change_achievement',
                                                                                        achievement) or checker.has_perm(
            'approve_achievement_lv2', achievement):
            return True

        if not user.is_authenticated:
            return False

        if user.role == RoleChoices.SECRETARY.value or user.role == RoleChoices.ADMIN.value or user.role == RoleChoices.DEV.value:
            return True
        return False


class ProcessViewSet(viewsets.ModelViewSet):
    queryset = Process.objects.all()
    serializer_class = ProcessSerializer

    @action(detail=False, url_path='get-process-by-achievement', methods=['post'])
    def get_process_by_achievement(self, request, *args, **kwargs):
        content_type_object = ContentType.objects.get(app_label=Achievement._meta.app_label,
                                                      model=Achievement._meta.model_name)
        achievement_id = request.data.get('achievement_id', 0)
        print(achievement_id)
        queryset = Process.objects.filter(artifact_content_type=content_type_object, artifact_object_id=achievement_id)
        print(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    #
    @action(detail=False, url_path='get-user-tasks')
    @permission_classes([IsAuthenticated])
    def get_user_tasks(self, request, *args, **kwargs):
        user = request.user
        queryset = Task.objects.filter(
            status=STATUS.ASSIGNED,
            owner=user.id,
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, url_path='user-has-missions')
    @permission_classes([IsAuthenticated])
    def user_has_missions(self, request, *args, **kwargs):
        user = request.user
        exists = Task.objects.filter(
            status=STATUS.ASSIGNED,
            owner=user.id,
        ).exists()
        return Response({'exists': exists == 1}, status=200)
