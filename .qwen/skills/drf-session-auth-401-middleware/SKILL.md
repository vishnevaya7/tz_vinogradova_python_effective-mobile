---
name: drf-session-auth-401-middleware
description: DRF с SessionAuthentication возвращает 403 вместо 401 для неаутентифицированных запросов — middleware для принудительного 401
source: auto-skill
extracted_at: '2026-06-16T12:32:41.525Z'
---

# DRF: принудительный 401 для неаутентифицированных запросов при SessionAuthentication

## Симптомы

Django REST Framework с `SessionAuthentication` при отсутствии сессии возвращает **403 Forbidden** вместо ожидаемого **401 Unauthorized**, даже если в кастомном `BasePermission.has_permission()` явно вызывается `raise NotAuthenticated()` или возвращается `False`. Сообщение: `{"detail":"Authentication credentials were not provided."}`, но статус — 403.

## Корневая причина

DRF-метод `APIView.permission_denied()` проверяет `request.successful_authenticator`. По неизвестной причине (возможно, из-за особенностей `DEFAULT_PERMISSION_CLASSES` или взаимодействия с Django `AuthenticationMiddleware`) этот атрибут оказывается truthy даже при отсутствии сессии, и DRF вызывает `PermissionDenied` (403) вместо `NotAuthenticated` (401).

**Why:** внутренняя логика DRF для различения 401/403 опирается на `successful_authenticator`, который ведёт себя неочевидно при использовании только `SessionAuthentication` без дополнительных аутентификаторов.

**How to apply:** в любом DRF-проекте, где используется `SessionAuthentication` и требуется строгое соблюдение HTTP-семантики (401 — нет сессии, 403 — есть сессия, но нет прав), добавлять middleware для коррекции статус-кода.

## Решение: кастомный middleware

Создать `core/middleware.py`:

```python
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
```

Подключить в `settings.py` **после** `AuthenticationMiddleware`:

```python
MIDDLEWARE = [
    ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.AuthStatusCodeMiddleware',   # ← после auth, до всего остального
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

## Почему это работает

`AuthenticationMiddleware` заполняет `request.user` (AnonymousUser или реальный пользователь). Middleware работает на **ответе** (post-response фаза): если DRF уже вернул 403, но пользователь — AnonymousUser, статус заменяется на 401. Аутентифицированные пользователи с реальным отсутствием прав по-прежнему получают 403.

## Что НЕ сработало (попытки, от которых отказались)

1. **`raise NotAuthenticated()` в `has_permission()`** — DRF всё равно конвертирует в 403.
2. **`AuthStatusMixin` с переопределением `permission_denied()`** — метод не вызывается или не даёт эффекта.
3. **Удаление `DEFAULT_PERMISSION_CLASSES`** — недостаточно для решения проблемы.
4. **Явное указание `permission_classes` на каждой view** — не влияет на поведение `permission_denied`.
