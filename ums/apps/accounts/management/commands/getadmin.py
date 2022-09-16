from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from ums.apps.accounts.utils import RoleChoices

User = get_user_model()


class Command(BaseCommand):
    help = '刷admin权限'

    def handle(self, *args, **options):
        queryset = User.objects.filter(
            role=RoleChoices.ADMIN.value
        )
        for user in queryset:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Admin user name :{user.name} id :{user.id}'
                )
            )
