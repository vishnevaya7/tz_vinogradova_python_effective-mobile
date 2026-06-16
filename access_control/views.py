from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from access_control.models import Action, Resource, Role, RolePermission, UserRole
from access_control.permissions import AuthStatusMixin, ResourceAccessPermission
from access_control.serializers import (
    ActionSerializer,
    ResourceSerializer,
    RolePermissionSerializer,
    RoleSerializer,
    UserRoleSerializer,
)


# ── Базовый ViewSet с динамическим маппингом HTTP → action ──────

class ResourceViewSetMixin:
    """Маппит HTTP-методы в required_action для ResourceAccessPermission."""

    def check_permissions(self, request):
        action_map = {
            'list': 'read',
            'retrieve': 'read',
            'create': 'write',
            'update': 'write',
            'partial_update': 'write',
            'destroy': 'delete',
        }
        self.required_action = action_map.get(self.action, 'read')
        super().check_permissions(request)


# ── Admin CRUD: Role ──────────────────────────────────────────────

class RoleViewSet(AuthStatusMixin, ResourceViewSetMixin, viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = (ResourceAccessPermission,)
    required_resource = 'permissions'


# ── Admin CRUD: Resource ──────────────────────────────────────────

class ResourceViewSet(AuthStatusMixin, ResourceViewSetMixin, viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = (ResourceAccessPermission,)
    required_resource = 'permissions'


# ── Admin CRUD: Action ────────────────────────────────────────────

class ActionViewSet(AuthStatusMixin, ResourceViewSetMixin, viewsets.ModelViewSet):
    queryset = Action.objects.all()
    serializer_class = ActionSerializer
    permission_classes = (ResourceAccessPermission,)
    required_resource = 'permissions'


# ── Admin CRUD: RolePermission ────────────────────────────────────

class RolePermissionViewSet(AuthStatusMixin, ResourceViewSetMixin, viewsets.ModelViewSet):
    queryset = RolePermission.objects.select_related('role', 'resource', 'action')
    serializer_class = RolePermissionSerializer
    permission_classes = (ResourceAccessPermission,)
    required_resource = 'permissions'


# ── Admin CRUD: UserRole ──────────────────────────────────────────

class UserRoleViewSet(AuthStatusMixin, ResourceViewSetMixin, viewsets.ModelViewSet):
    queryset = UserRole.objects.select_related('user', 'role')
    serializer_class = UserRoleSerializer
    permission_classes = (ResourceAccessPermission,)
    required_resource = 'permissions'


# ── Mock business objects ─────────────────────────────────────────

MOCK_DOCUMENTS = [
    {'id': 1, 'title': 'Договор №1', 'status': 'подписан'},
    {'id': 2, 'title': 'Счет-фактура №42', 'status': 'оплачен'},
    {'id': 3, 'title': 'Акт приема-передачи', 'status': 'на согласовании'},
]

MOCK_REPORTS = [
    {'id': 1, 'title': 'Отчет по продажам Q1', 'author': 'Иванов И.И.'},
    {'id': 2, 'title': 'Финансовый отчет 2025', 'author': 'Петров П.П.'},
    {'id': 3, 'title': 'Анализ рынка', 'author': 'Сидоров С.С.'},
]


class DocumentListView(AuthStatusMixin, APIView):
    required_resource = 'document'
    required_action = 'read'
    permission_classes = (ResourceAccessPermission,)

    def get(self, request):
        return Response(MOCK_DOCUMENTS)


class ReportListView(AuthStatusMixin, APIView):
    required_resource = 'report'
    required_action = 'read'
    permission_classes = (ResourceAccessPermission,)

    def get(self, request):
        return Response(MOCK_REPORTS)
