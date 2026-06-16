from django.http import JsonResponse
from django.urls import include, path


def api_root(request):
    return JsonResponse({
        'auth': {
            'register': '/api/auth/register/',
            'login': '/api/auth/login/',
            'logout': '/api/auth/logout/',
            'profile': '/api/auth/profile/',
            'delete': '/api/auth/delete/',
        },
        'mock_resources': {
            'documents': '/api/documents/',
            'reports': '/api/reports/',
        },
        'admin_api': {
            'roles': '/api/admin/roles/',
            'resources': '/api/admin/resources/',
            'actions': '/api/admin/actions/',
            'permissions': '/api/admin/permissions/',
        },
    })


urlpatterns = [
    path('', api_root, name='api-root'),
    path('api/auth/', include('users.urls')),
    path('api/', include('access_control.urls')),
]
