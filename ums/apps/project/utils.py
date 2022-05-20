from django.db import models
from django.utils.translation import gettext_lazy as _


class ProjectTypeChoices(models.TextChoices):
    FR = '0', _('前瞻研究')  # Frontend research
    PD = '1', _('策划规划设计')  # Plan & Design
    DC = '2', _('研讨竞赛')  # Research & Competition
    CS = '3', _('顾问咨询')  # Advisor & Consult


class ProjectCateChoices(models.TextChoices):
    IR = '0', _('创新研究')  # Innovation Research
    BS = '1', _('业务服务')  # Business Services


class ProjectStatusChoices(models.TextChoices):
    NEW = 'NEW', _('新创建')  # 新创建， 允许修改、删除, 允许上传成果
    START = 'START', _('成果上传中')  # non-editable, 允许上传成果
    END = 'END', _('项目结束')  # 不允许上传、审批成果，所有相关链接改为跳转，不允许下载
    LOCK = 'LOCK', _('项目锁定')  # 项目被锁定，与end一样，但是项目可能未结束


class AchievementStateChoices(models.TextChoices):
    NEW = '1', _('新创建')
    SUB = '2', _('已提交')
    APP = '3', _('审批通过')
    DENY = '4', _('审批驳回')
    WITHDRAW = '5', _('已撤销')





