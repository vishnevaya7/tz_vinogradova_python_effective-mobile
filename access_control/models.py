from django.conf import settings
from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'

    def __str__(self):
        return self.name


class Resource(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'Ресурс'
        verbose_name_plural = 'Ресурсы'

    def __str__(self):
        return self.name


class Action(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'Действие'
        verbose_name_plural = 'Действия'

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    action = models.ForeignKey(Action, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Право доступа'
        verbose_name_plural = 'Права доступа'
        unique_together = ('role', 'resource', 'action')

    def __str__(self):
        return f'{self.role} — {self.resource}:{self.action}'


class UserRole(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name='Пользователь',
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name='Роль',
    )
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата назначения')

    class Meta:
        verbose_name = 'Роль пользователя'
        verbose_name_plural = 'Роли пользователей'
        unique_together = ('user', 'role')

    def __str__(self):
        return f'{self.user} → {self.role}'
