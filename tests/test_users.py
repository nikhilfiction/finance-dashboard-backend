from django.urls import reverse
from rest_framework import status
from .utils import BaseAPITest, create_user, get_tokens_for_user
from users.models import Role


class RegistrationTests(BaseAPITest):
    url = '/api/v1/auth/register/'

    def test_register_success(self):
        res = self.client.post(self.url, {
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'Secure@1234',
            'password_confirm': 'Secure@1234',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertIn('tokens', res.data['data'])
        self.assertEqual(res.data['data']['user']['role'], 'viewer')  # default role

    def test_register_mismatched_passwords(self):
        res = self.client.post(self.url, {
            'email': 'x@test.com',
            'first_name': 'X', 'last_name': 'Y',
            'password': 'Secure@1234',
            'password_confirm': 'Wrong@1234',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        self.client.post(self.url, {
            'email': 'dup@test.com', 'first_name': 'A', 'last_name': 'B',
            'password': 'Secure@1234', 'password_confirm': 'Secure@1234',
        })
        res = self.client.post(self.url, {
            'email': 'dup@test.com', 'first_name': 'A', 'last_name': 'B',
            'password': 'Secure@1234', 'password_confirm': 'Secure@1234',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password(self):
        res = self.client.post(self.url, {
            'email': 'weak@test.com', 'first_name': 'A', 'last_name': 'B',
            'password': '123', 'password_confirm': '123',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(BaseAPITest):
    url = '/api/v1/auth/login/'

    def test_login_success(self):
        res = self.client.post(self.url, {'email': 'admin@test.com', 'password': 'testpass123'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertIn('access', res.data['data']['tokens'])

    def test_login_wrong_password(self):
        res = self.client.post(self.url, {'email': 'admin@test.com', 'password': 'wrongpass'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_inactive_user(self):
        inactive = create_user('inactive@test.com', is_active=False)
        res = self.client.post(self.url, {'email': 'inactive@test.com', 'password': 'testpass123'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unknown_email(self):
        res = self.client.post(self.url, {'email': 'nobody@test.com', 'password': 'testpass123'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class MeViewTests(BaseAPITest):
    url = '/api/v1/auth/me/'

    def test_get_profile_authenticated(self):
        self.auth(self.viewer)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['data']['email'], 'viewer@test.com')

    def test_get_profile_unauthenticated(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_name(self):
        self.auth(self.viewer)
        res = self.client.patch(self.url, {'first_name': 'Updated'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['data']['first_name'], 'Updated')


class AdminUserManagementTests(BaseAPITest):
    list_url = '/api/v1/users/'

    def detail_url(self, pk):
        return f'/api/v1/users/{pk}/'

    def test_admin_can_list_users(self):
        self.auth(self.admin)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_cannot_list_users(self):
        self.auth(self.viewer)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_analyst_cannot_list_users(self):
        self.auth(self.analyst)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_user(self):
        self.auth(self.admin)
        res = self.client.post(self.list_url, {
            'email': 'newanalyst@test.com',
            'first_name': 'Ana', 'last_name': 'Lyst',
            'role': 'analyst',
            'password': 'Secure@1234',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['data']['role'], 'analyst')

    def test_admin_can_update_user_role(self):
        self.auth(self.admin)
        res = self.client.patch(self.detail_url(self.viewer.pk), {'role': 'analyst'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.viewer.refresh_from_db()
        self.assertEqual(self.viewer.role, 'analyst')

    def test_admin_can_soft_delete_user(self):
        self.auth(self.admin)
        target = create_user('target@test.com')
        res = self.client.delete(self.detail_url(target.pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        target.refresh_from_db()
        self.assertFalse(target.is_active)

    def test_admin_cannot_delete_self(self):
        self.auth(self.admin)
        res = self.client.delete(self.detail_url(self.admin.pk))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_users_by_role(self):
        self.auth(self.admin)
        res = self.client.get(self.list_url + '?role=viewer')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for user in res.data['data']:
            self.assertEqual(user['role'], 'viewer')
