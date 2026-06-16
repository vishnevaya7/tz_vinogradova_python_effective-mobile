from rest_framework import exceptions, permissions

from access_control.models import RolePermission


class AuthStatusMixin:
    """Mixin: при отсутствии аутентификации → 401, иначе → 403."""

    def permission_denied(self, request, message=None, code=None):
        if not request.user or not request.user.is_authenticated:
            raise exceptions.NotAuthenticated()
        raise exceptions.PermissionDenied(message, code)


class ResourceAccessPermission(permissions.BasePermission):
    """
    Проверяет:
    - пользователь аутентифицирован → иначе 401 (через DRF permission_denied)
    - у пользователя есть роль → иначе 403
    - роль имеет разрешение на ресурс и действие → иначе 403
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        resource = getattr(view, 'required_resource', None)
        action = getattr(view, 'required_action', 'read')

        if resource is None:
            return False

        role = request.user.role
        if role is None:
            return False

        return RolePermission.objects.filter(
            role=role,
            resource__name=resource,
            action__name=action,
        ).exists()


class IsAdminRole(permissions.BasePermission):
    """Доступ только для пользователей с ролью admin."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = request.user.role
        return role is not None and role.name == 'admin'
