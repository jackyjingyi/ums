from django.db import models
from django.utils.translation import gettext_lazy as _


class RoleChoices(models.IntegerChoices):
    SECRETARY = 1
    PROJECT_WORKER = 2
    PROJECT_SPONSOR = 3
    APPROVAL_LEADER = 4
    ADMIN = 5
    DEV = 6
    LEADER = 7
    ANON = -1


class GroupTypeChoices(models.TextChoices):
    RT = 'RT', _('团组')  # research team
    DP = 'DP', _('部门')  # department
