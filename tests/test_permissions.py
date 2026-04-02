"""
Tests for role-based permission logic independent of specific endpoints.
"""
from django.test import TestCase, RequestFactory
from unittest.mock import MagicMock
from users.models import Role
from users.permissions import IsAdmin, IsAnalystOrAdmin, IsAnyAuthenticatedRole, IsAdminOrReadOnly
from .utils import create_user


def make_request(method='GET', user=None):
    factory = RequestFactory()
    req = getattr(factory, method.lower())('/')
    req.user = user or MagicMock()
    return req


class IsAdminPermissionTests(TestCase):

    def test_admin_granted(self):
        user = create_user('a@p.com', role=Role.ADMIN)
        req = make_request(user=user)
        self.assertTrue(IsAdmin().has_permission(req, None))

    def test_analyst_denied(self):
        user = create_user('b@p.com', role=Role.ANALYST)
        req = make_request(user=user)
        self.assertFalse(IsAdmin().has_permission(req, None))

    def test_viewer_denied(self):
        user = create_user('c@p.com', role=Role.VIEWER)
        req = make_request(user=user)
        self.assertFalse(IsAdmin().has_permission(req, None))

    def test_inactive_admin_denied(self):
        user = create_user('d@p.com', role=Role.ADMIN, is_active=False)
        req = make_request(user=user)
        self.assertFalse(IsAdmin().has_permission(req, None))


class IsAnalystOrAdminTests(TestCase):

    def test_admin_granted(self):
        user = create_user('aa@p.com', role=Role.ADMIN)
        req = make_request(user=user)
        self.assertTrue(IsAnalystOrAdmin().has_permission(req, None))

    def test_analyst_granted(self):
        user = create_user('ab@p.com', role=Role.ANALYST)
        req = make_request(user=user)
        self.assertTrue(IsAnalystOrAdmin().has_permission(req, None))

    def test_viewer_denied(self):
        user = create_user('ac@p.com', role=Role.VIEWER)
        req = make_request(user=user)
        self.assertFalse(IsAnalystOrAdmin().has_permission(req, None))


class IsAdminOrReadOnlyTests(TestCase):

    def test_admin_write_granted(self):
        user = create_user('ra@p.com', role=Role.ADMIN)
        req = make_request('POST', user=user)
        self.assertTrue(IsAdminOrReadOnly().has_permission(req, None))

    def test_viewer_read_granted(self):
        user = create_user('rv@p.com', role=Role.VIEWER)
        req = make_request('GET', user=user)
        self.assertTrue(IsAdminOrReadOnly().has_permission(req, None))

    def test_viewer_write_denied(self):
        user = create_user('rw@p.com', role=Role.VIEWER)
        req = make_request('POST', user=user)
        self.assertFalse(IsAdminOrReadOnly().has_permission(req, None))

    def test_analyst_write_denied(self):
        user = create_user('ran@p.com', role=Role.ANALYST)
        req = make_request('DELETE', user=user)
        self.assertFalse(IsAdminOrReadOnly().has_permission(req, None))

    def test_analyst_read_granted(self):
        user = create_user('rag@p.com', role=Role.ANALYST)
        req = make_request('GET', user=user)
        self.assertTrue(IsAdminOrReadOnly().has_permission(req, None))
