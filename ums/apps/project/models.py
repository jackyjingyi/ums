import hashlib
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.template import Template, Context
from django.utils.encoding import force_str
from django.contrib.auth.models import Group, Permission, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from jsonstore import JSONField
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase
from ..accounts.utils import RoleChoices
from .activation import STATUS, STATUS_CHOICES
from .utils import ProjectTypeChoices, ProjectCateChoices, ProjectStatusChoices, AchievementStateChoices, \
    ContractChoices


class Project(models.Model):
    project_id = models.CharField(_('合同编号'), max_length=255, unique=True)
    project_title = models.CharField(_('项目名称'), max_length=255)
    project_type = models.CharField(_('项目类型'), choices=ProjectTypeChoices.choices, max_length=10)
    project_cate = models.CharField(_('项目类型'), choices=ProjectCateChoices.choices, max_length=10)
    project_members = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name=_('项目组成员'), db_index=True,
                                             related_name='member', related_query_name='project_member',
                                             limit_choices_to={
                                                 'role__in': [RoleChoices.PROJECT_SPONSOR.value,
                                                              RoleChoices.PROJECT_WORKER.value,
                                                              RoleChoices.SECRETARY.value, RoleChoices.ADMIN.value]})
    project_created = models.DateTimeField(_('项目创建时间'), auto_now_add=True, blank=True)
    project_sponsor = models.ManyToManyField(
        settings.AUTH_USER_MODEL, db_index=True,
        verbose_name=_('负责人'), related_name='project_sponsor',
        related_query_name='project_responsible_for',
    )
    project_approver = models.ManyToManyField(
        settings.AUTH_USER_MODEL, db_index=True,
        verbose_name=_('审批人'), related_name='project_approver',
        related_query_name='project_approval_to',
        limit_choices_to={'role': RoleChoices.APPROVAL_LEADER.value}
    )
    project_issuer = models.ForeignKey(
        settings.AUTH_USER_MODEL, db_index=True, on_delete=models.CASCADE,
        verbose_name=_('创建人'), related_name='project_issuer',
        related_query_name='project_issued',
        # limit_choices_to={'role': RoleChoices.SECRETARY.value}
    )
    status = models.CharField(
        _('项目状态'), choices=ProjectStatusChoices.choices, max_length=10, db_index=True,
        default=ProjectStatusChoices.NEW.value
    )

    class Meta:
        ordering = ['-project_created']


class Achievement(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name=_('项目编号'))
    name = models.CharField(_('成果名称'), max_length=25)
    stage = models.CharField(_('工作阶段'), max_length=255, null=True, blank=True)
    output_list = models.CharField(_('成果清单'), max_length=255, null=True, blank=True)
    contract_type = models.CharField('合同类型', choices=ContractChoices.choices, default=ContractChoices.MAIN.value,
                                     db_index=True, max_length=5)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achievement_creator')
    created = models.DateTimeField(_('创建时间'), auto_now_add=True, null=True)
    updated = models.DateTimeField(_('更新时间'), auto_now=True, null=True)
    state = models.CharField(_('流程状态'), max_length=5, choices=AchievementStateChoices.choices,
                             default=AchievementStateChoices.NEW.value, db_index=True)
    status1 = models.CharField(_('一级审批状态'), max_length=25, default=STATUS.NEW)
    status2 = models.CharField(_('二级审批状态'), max_length=25, default=STATUS.NEW)
    is_finished = models.BooleanField(default=False, help_text='流程走完，需要商务秘书及时review', db_index=True)
    is_reviewed = models.BooleanField(default=False, help_text='对接展示', db_index=True)

    class Meta:
        ordering = ['-created', '-updated']
        permissions = [('submit_achievement', 'Can submit achievement'),
                       ('withdraw_achievement', 'Can withdraw achievement'),
                       ('approve_achievement_lv1', 'Can approve achievement lv1'),
                       ('approve_achievement_lv2', 'Can approve achievement lv2'),
                       ('final_review_achievement', 'Can final review achievement')
                       ]

    def get_project_name(self):
        return self.project.name

    def get_project_sponsor(self):
        return self.project.project_sponsor.all()

    def get_project_leader(self):
        return self.project.project_approver.all()


class TaggedFile(TaggedItemBase):
    content_object = models.ForeignKey('FileManager', on_delete=models.CASCADE)


def achievement_file_name(instance, filename):
    return f"""project/achievement/{hashlib.md5((str(instance.achievement).encode('UTF-8'))).hexdigest()}/{filename}"""


class FileManager(models.Model):
    achievement = models.ForeignKey(
        Achievement, on_delete=models.CASCADE, verbose_name=_('成果文件'), related_name='files', db_index=True
    )
    name = models.CharField(_('文件名'), max_length=255, null=True, blank=True)
    file = models.FileField(
        upload_to=achievement_file_name, null=True
    )
    # todo 标签
    created = models.DateTimeField(_('创建时间'), auto_now_add=True, null=True)
    updated = models.DateTimeField(_('更新时间'), auto_now=True, null=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, db_index=True,
        on_delete=models.CASCADE, verbose_name=_('文件上传人'), related_name='outcome_owner'
    )
    tags = TaggableManager(verbose_name=_('标签'), through=TaggedFile)
    file_link = models.CharField(_('展示链接'), max_length=255, default='')


class AbsProcess(models.Model):
    status = models.CharField(_('Status'), max_length=50, default=STATUS.NEW)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    finished = models.DateTimeField(_('Finished'), blank=True, null=True)

    class Meta:
        abstract = True


class AbsTask(models.Model):
    flow_task_type = models.CharField(_('Type'), max_length=50)
    status = models.CharField(_('Status'), max_length=50, default=STATUS.NEW, db_index=True)

    created = models.DateTimeField(_('Created'), auto_now_add=True)
    assigned = models.DateTimeField(_('Assigned'), blank=True, null=True)
    started = models.DateTimeField(_('Started'), blank=True, null=True)
    finished = models.DateTimeField('Finished', blank=True, null=True)
    previous = models.ManyToManyField('self', symmetrical=False, related_name='leading', verbose_name=_('Previous'))

    class Meta:
        abstract = True


class Process(AbsProcess):
    artifact_content_type = models.ForeignKey(
        ContentType, null=True, blank=True,
        on_delete=models.CASCADE, related_name='+'
    )
    artifact_object_id = models.PositiveIntegerField(null=True, blank=True)
    artifact = GenericForeignKey('artifact_content_type', 'artifact_object_id')

    data = JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-finished', '-id', '-created']
        verbose_name = _('Process')
        verbose_name_plural = _('Process list')
        indexes = [
            models.Index(
                fields=["artifact_content_type", "artifact_object_id"]
            )
        ]


class Task(AbsTask):
    process = models.ForeignKey(Process, on_delete=models.CASCADE, verbose_name=_('Process'), related_name='task',
                                related_query_name='tasks')

    artifact_content_type = models.ForeignKey(
        ContentType, null=True, blank=True,
        on_delete=models.CASCADE, related_name='+'
    )
    artifact_object_id = models.PositiveIntegerField(null=True, blank=True)
    artifact = GenericForeignKey('artifact_content_type', 'artifact_object_id')

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, db_index=True,
        on_delete=models.CASCADE, verbose_name=_('Owner'), related_name='project_task_owner')
    external_task_id = models.CharField(_('External Task ID'), max_length=50, blank=True, null=True, db_index=True)
    owner_permission = models.CharField(_('Permission'), max_length=255, blank=True, null=True)
    comments = models.TextField(_('Comments'), blank=True, null=True)

    data = JSONField(null=True, blank=True)

    class Meta:  # noqa D101
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')
        ordering = ['id', 'finished']
        indexes = [
            models.Index(
                fields=["artifact_content_type", "artifact_object_id"]
            )
        ]
