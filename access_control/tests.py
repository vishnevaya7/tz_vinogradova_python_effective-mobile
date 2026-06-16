from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from access_control.models import Action, Resource, Role, RolePermission, UserRole
from users.models import AuthToken, CustomUser
from users.authentication import generate_token


@override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
class AccessControlTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Справочники
        self.role_admin = Role.objects.create(name='admin')
        self.role_user = Role.objects.create(name='user')
        self.resource_doc = Resource.objects.create(name='document')
        self.resource_rep = Resource.objects.create(name='report')
        self.resource_perm = Resource.objects.create(name='permissions')
        self.action_read = Action.objects.create(name='read')
        self.action_write = Action.objects.create(name='write')
        self.action_delete = Action.objects.create(name='delete')

        # Права: admin → всё на document/report/permissions, user → read на document/report
        for res in (self.resource_doc, self.resource_rep, self.resource_perm):
            for act in (self.action_read, self.action_write, self.action_delete):
                RolePermission.objects.create(role=self.role_admin, resource=res, action=act)
        RolePermission.objects.create(role=self.role_user, resource=self.resource_doc, action=self.action_read)
        RolePermission.objects.create(role=self.role_user, resource=self.resource_rep, action=self.action_read)

        # Пользователи
        self.admin = CustomUser.objects.create_user(
            email='admin@example.com',
            first_name='Админ',
            last_name='Админов',
            password='password',
        )
        self.user = CustomUser.objects.create_user(
            email='user@example.com',
            first_name='Юзер',
            last_name='Юзеров',
            password='password',
        )
        self.no_role_user = CustomUser.objects.create_user(
            email='norole@example.com',
            first_name='Без',
            last_name='Роли',
            password='password',
        )

        UserRole.objects.create(user=self.admin, role=self.role_admin)
        UserRole.objects.create(user=self.user, role=self.role_user)

    def _auth_header(self, token):
        return {'HTTP_AUTHORIZATION': f'Token {token}'}

    def _login(self, email, password='password'):
        response = self.client.post('/api/auth/login/', {'email': email, 'password': password})
        return response.data['token']

    # ── Mock-объекты: доступ ────────────────────────────────

    def test_admin_can_read_documents(self):
        token = self._login('admin@example.com')
        response = self.client.get('/api/documents/', **self._auth_header(token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_user_can_read_documents(self):
        token = self._login('user@example.com')
        response = self.client.get('/api/documents/', **self._auth_header(token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_user_can_read_reports(self):
        token = self._login('user@example.com')
        response = self.client.get('/api/reports/', **self._auth_header(token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_admin_can_read_reports(self):
        token = self._login('admin@example.com')
        response = self.client.get('/api/reports/', **self._auth_header(token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    # ── 401 / 403 ───────────────────────────────────────────

    def test_documents_401_without_auth(self):
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_documents_403_no_role(self):
        token = self._login('norole@example.com')
        response = self.client.get('/api/documents/', **self._auth_header(token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reports_403_when_role_lacks_permission(self):
        token = self._login('norole@example.com')
        response = self.client.get('/api/reports/', **self._auth_header(token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ── Admin API ───────────────────────────────────────────

    def test_admin_can_list_roles(self):
        token = self._login('admin@example.com')
        response = self.client.get('/api/admin/roles/', **self._auth_header(token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_admin_can_create_permission(self):
        token = self._login('admin@example.com')
        response = self.client.post('/api/admin/permissions/', {
            'role': self.role_user.pk,
            'resource': self.resource_rep.pk,
            'action': self.action_write.pk,
        }, **self._auth_header(token))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            RolePermission.objects.filter(
                role=self.role_user,
                resource=self.resource_rep,
                action=self.action_write,
            ).exists()
        )

    def test_admin_can_delete_permission(self):
        token = self._login('admin@example.com')
        perm = RolePermission.objects.get(
            role=self.role_user,
            resource=self.resource_doc,
            action=self.action_read,
        )
        response = self.client.delete(
            f'/api/admin/permissions/{perm.pk}/',
            **self._auth_header(token),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(RolePermission.objects.filter(pk=perm.pk).exists())

    def test_non_admin_cannot_access_admin_api(self):
        token = self._login('user@example.com')
        response = self.client.get('/api/admin/roles/', **self._auth_header(token))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_role(self):
        token = self._login('admin@example.com')
        response = self.client.post('/api/admin/roles/', {'name': 'editor'}, **self._auth_header(token))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Role.objects.filter(name='editor').exists())

    def test_admin_can_create_resource(self):
        token = self._login('admin@example.com')
        response = self.client.post('/api/admin/resources/', {'name': 'invoice'}, **self._auth_header(token))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Resource.objects.filter(name='invoice').exists())

    def test_admin_can_create_action(self):
        token = self._login('admin@example.com')
        response = self.client.post('/api/admin/actions/', {'name': 'approve'}, **self._auth_header(token))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Action.objects.filter(name='approve').exists())

    def test_duplicate_permission_rejected(self):
        token = self._login('admin@example.com')
        response = self.client.post('/api/admin/permissions/', {
            'role': self.role_admin.pk,
            'resource': self.resource_doc.pk,
            'action': self.action_read.pk,
        }, **self._auth_header(token))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── UserRole CRUD ───────────────────────────────────────

    def test_admin_can_assign_role_to_user(self):
        token = self._login('admin@example.com')
        response = self.client.post('/api/admin/user-roles/', {
            'user': self.no_role_user.pk,
            'role': self.role_user.pk,
        }, **self._auth_header(token))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            UserRole.objects.filter(user=self.no_role_user, role=self.role_user).exists()
        )

    def test_admin_can_list_user_roles(self):
        token = self._login('admin@example.com')
        response = self.client.get('/api/admin/user-roles/', **self._auth_header(token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_duplicate_user_role_rejected(self):
        token = self._login('admin@example.com')
        response = self.client.post('/api/admin/user-roles/', {
            'user': self.admin.pk,
            'role': self.role_admin.pk,
        }, **self._auth_header(token))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
