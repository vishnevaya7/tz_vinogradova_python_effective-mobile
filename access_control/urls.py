from django.urls import include, path
from rest_framework.routers import DefaultRouter

from access_control import views

router = DefaultRouter()
router.register(r'admin/roles', views.RoleViewSet, basename='role')
router.register(r'admin/resources', views.ResourceViewSet, basename='resource')
router.register(r'admin/actions', views.ActionViewSet, basename='action')
router.register(r'admin/permissions', views.RolePermissionViewSet, basename='permission')

urlpatterns = [
    path('', include(router.urls)),
    path('documents/', views.DocumentListView.as_view(), name='documents'),
    path('reports/', views.ReportListView.as_view(), name='reports'),
]
