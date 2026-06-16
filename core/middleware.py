from django.http import JsonResponse


class AuthStatusCodeMiddleware:
    """Если запрос вернул 403 и пользователь не аутентифицирован — меняем на 401."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code == 403 and not request.user.is_authenticated:
            return JsonResponse(
                {'detail': 'Authentication credentials were not provided.'},
                status=401,
            )

        return response
