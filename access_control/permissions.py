from rest_framework import exceptions, permissions

from access_control.models import RolePermission, UserRole


class AuthStatusMixin:
    """Mixin: при отсутствии аутентификации → 401, иначе → 403."""

    def permission_denied(self, request, message=None, code=None):
        if not request.user or not request.user.is_authenticated:
            raise exceptions.NotAuthenticated()
        raise exceptions.PermissionDenied(message, code)


class ResourceAccessPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        resource = getattr(view, 'required_resource', None)
        action = getattr(view, 'required_action', 'read')

        if resource is None:
            return False

        user_role_ids = UserRole.objects.filter(
            user=request.user,
        ).values_list('role_id', flat=True)

        if not user_role_ids:
            return False

        return RolePermission.objects.filter(
            role_id__in=user_role_ids,
            resource__name=resource,
            action__name=action,
        ).exists()
