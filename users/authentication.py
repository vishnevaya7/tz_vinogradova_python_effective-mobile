import secrets

from rest_framework import authentication, exceptions

from users.models import AuthToken


def generate_token():
    return secrets.token_hex(32)


class TokenAuthentication(authentication.BaseAuthentication):
    keyword = 'Token'

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header:
            return None

        try:
            keyword, key = auth_header.split()
        except ValueError:
            raise exceptions.AuthenticationFailed('Неверный формат заголовка Authorization')

        if keyword.lower() != self.keyword.lower():
            return None

        try:
            token = AuthToken.objects.select_related('user').get(key=key)
        except AuthToken.DoesNotExist:
            raise exceptions.AuthenticationFailed('Недействительный токен')

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed('Учётная запись деактивирована')

        return (token.user, token)
