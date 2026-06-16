from django.core.management.base import BaseCommand

from access_control.models import Action, Resource, Role, RolePermission
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Заполнение БД тестовыми данными: роли, права, пользователи'

    def handle(self, *args, **options):
        # ── Справочники ──────────────────────────────────────
        roles = {}
        for name in ('admin', 'manager', 'user'):
            roles[name], _ = Role.objects.get_or_create(name=name)

        resources = {}
        for name in ('document', 'report'):
            resources[name], _ = Resource.objects.get_or_create(name=name)

        actions = {}
        for name in ('read', 'write', 'delete'):
            actions[name], _ = Action.objects.get_or_create(name=name)

        # ── Права доступа ────────────────────────────────────
        permissions = {
            'admin': [
                ('document', 'read'), ('document', 'write'), ('document', 'delete'),
                ('report', 'read'), ('report', 'write'), ('report', 'delete'),
            ],
            'manager': [
                ('document', 'read'), ('document', 'write'),
                ('report', 'read'), ('report', 'write'),
            ],
            'user': [
                ('document', 'read'),
                ('report', 'read'),
            ],
        }

        for role_name, perms in permissions.items():
            for resource_name, action_name in perms:
                RolePermission.objects.get_or_create(
                    role=roles[role_name],
                    resource=resources[resource_name],
                    action=actions[action_name],
                )

        # ── Пользователи ─────────────────────────────────────
        users_data = [
            ('admin@example.com', 'admin', 'Админ', 'Админов'),
            ('manager@example.com', 'manager', 'Менеджер', 'Менеджеров'),
            ('user@example.com', 'user', 'Пользователь', 'Обычный'),
        ]

        for email, role_name, first_name, last_name in users_data:
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': roles[role_name],
                    'is_active': True,
                },
            )
            if created:
                user.set_password('password')
                user.save()
                self.stdout.write(f'Создан пользователь: {email} ({role_name})')
            else:
                self.stdout.write(f'Пользователь уже существует: {email}')

        self.stdout.write(self.style.SUCCESS('Тестовые данные загружены.'))
