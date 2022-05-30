from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from ums.apps.accounts.utils import RoleChoices

User = get_user_model()


class Command(BaseCommand):

    help = '刷admin权限'

    def add_arguments(self, parser):
        parser.add_argument('user_ids', nargs='+', type=int)

        parser.add_argument(
            '--setPermissions',
            action='store_true',
            help='为用户添加相关权限'
        )

    def handle(self, *args, **options):
        for user_id in options['user_ids']:
            try:
                user = User.objects.get(
                    id=user_id
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'user name :{user.name} id :{user.id} phone: {user.phone_number} role:{user.get_role_display()}'
                    )
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'User {user_id} does not exist'
                    )
                )
                continue

