from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from access_control.models import Role
from users.models import CustomUser


@override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
class AuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        self.logout_url = '/api/auth/logout/'
        self.profile_url = '/api/auth/profile/'
        self.delete_url = '/api/auth/delete/'

        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Иван',
            'last_name': 'Петров',
            'password': 'qwerty123',
            'password_repeat': 'qwerty123',
        }

    # ── Регистрация ─────────────────────────────────────────

    def test_register_success(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertTrue(CustomUser.objects.filter(email='test@example.com').exists())

    def test_register_password_mismatch(self):
        data = {**self.user_data, 'password_repeat': 'different'}
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_repeat', response.data)

    def test_register_short_password(self):
        data = {**self.user_data, 'password': '123', 'password_repeat': '123'}
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_register_duplicate_email(self):
        self.client.post(self.register_url, self.user_data)
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    # ── Login ───────────────────────────────────────────────

    def _register_and_login(self, email=None, password=None):
        if email is None:
            email = self.user_data['email']
        if password is None:
            password = self.user_data['password']
        user_data = {**self.user_data, 'email': email, 'password': password, 'password_repeat': password}
        self.client.post(self.register_url, user_data)
        return self.client.post(self.login_url, {'email': email, 'password': password})

    def test_login_success(self):
        response = self._register_and_login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_login_wrong_password(self):
        self.client.post(self.register_url, self.user_data)
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'wrong',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_login_nonexistent_email(self):
        response = self.client.post(self.login_url, {
            'email': 'nobody@example.com',
            'password': 'password',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_login_deactivated_user(self):
        response = self._register_and_login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.delete(self.delete_url)
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'qwerty123',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    # ── Logout ──────────────────────────────────────────────

    def test_logout(self):
        self._register_and_login()
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logout_without_auth(self):
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Профиль ─────────────────────────────────────────────

    def test_get_profile(self):
        self._register_and_login()
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_get_profile_without_auth(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile(self):
        self._register_and_login()
        response = self.client.put(self.profile_url, {
            'first_name': 'Новое',
            'last_name': 'Имя',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Новое')
        self.assertEqual(response.data['last_name'], 'Имя')

    def test_cannot_update_email(self):
        self._register_and_login()
        response = self.client.put(self.profile_url, {
            'first_name': 'Иван',
            'last_name': 'Петров',
            'email': 'hacked@example.com',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')

    # ── Мягкое удаление ─────────────────────────────────────

    def test_soft_delete(self):
        self._register_and_login()
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        user = CustomUser.objects.get(email='test@example.com')
        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.pk)

    def test_soft_delete_without_auth(self):
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
