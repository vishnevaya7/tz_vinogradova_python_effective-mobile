from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from access_control.models import Action, Resource, Role, RolePermission
from access_control.permissions import AuthStatusMixin, IsAdminRole, ResourceAccessPermission
from access_control.serializers import (
    ActionSerializer,
    ResourceSerializer,
    RolePermissionSerializer,
    RoleSerializer,
)


# ── Admin CRUD: Role ──────────────────────────────────────────────

class RoleViewSet(AuthStatusMixin, viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = (permissions.IsAuthenticated, IsAdminRole)


# ── Admin CRUD: Resource ──────────────────────────────────────────

class ResourceViewSet(AuthStatusMixin, viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = (permissions.IsAuthenticated, IsAdminRole)


# ── Admin CRUD: Action ────────────────────────────────────────────

class ActionViewSet(AuthStatusMixin, viewsets.ModelViewSet):
    queryset = Action.objects.all()
    serializer_class = ActionSerializer
    permission_classes = (permissions.IsAuthenticated, IsAdminRole)


# ── Admin CRUD: RolePermission ────────────────────────────────────

class RolePermissionViewSet(AuthStatusMixin, viewsets.ModelViewSet):
    queryset = RolePermission.objects.select_related('role', 'resource', 'action')
    serializer_class = RolePermissionSerializer
    permission_classes = (permissions.IsAuthenticated, IsAdminRole)


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
