"""
Shared test utilities and base test class.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from datetime import date

from users.models import User, Role
from records.models import FinancialRecord, RecordType, Category


def create_user(email, password='testpass123', role=Role.VIEWER, is_active=True, **kwargs):
    return User.objects.create_user(
        email=email, password=password, role=role,
        first_name='Test', last_name='User',
        is_active=is_active, **kwargs
    )


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


def create_record(record_type=RecordType.INCOME, category=Category.SALARY,
                  amount=Decimal('1000.00'), record_date=None, created_by=None, **kwargs):
    return FinancialRecord.objects.create(
        record_type=record_type,
        category=category,
        amount=amount,
        date=record_date or date.today(),
        description='Test record',
        created_by=created_by,
        **kwargs,
    )


class BaseAPITest(TestCase):
    """Base test class with helpers for authenticated API calls."""

    def setUp(self):
        self.client = APIClient()
        self.admin = create_user('admin@test.com', role=Role.ADMIN)
        self.analyst = create_user('analyst@test.com', role=Role.ANALYST)
        self.viewer = create_user('viewer@test.com', role=Role.VIEWER)

    def auth(self, user):
        tokens = get_tokens_for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        return tokens

    def unauth(self):
        self.client.credentials()
