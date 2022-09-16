from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from ums.apps.accounts.utils import RoleChoices
from ums.apps.project.models import Project

User = get_user_model()


class Command(BaseCommand):
    help = '刷admin权限'

    def handle(self, *args, **options):
        queryset = User.objects.filter(
            role=RoleChoices.SECRETARY.value
        )
        content_type = ContentType.objects.get_for_model(Project)
        permissions = Permission.objects.filter(content_type=content_type,
                                                codename__in=['add_project', 'change_project', 'view_project',
                                                              'delete_project'])
        for user in queryset:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Secretary user name :{user.name} id :{user.id}'
                )
            )
            for perm in permissions:
                user.user_permissions.add(perm)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Secretary user name :{user.name} id :{user.id} add {perm}'
                    )
                )
