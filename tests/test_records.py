from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta

from records.models import FinancialRecord, RecordType, Category
from .utils import BaseAPITest, create_record


class RecordListTests(BaseAPITest):
    url = '/api/v1/records/'

    def setUp(self):
        super().setUp()
        self.r1 = create_record(
            record_type=RecordType.INCOME, category=Category.SALARY,
            amount=Decimal('5000.00'), record_date=date.today(),
            created_by=self.admin,
        )
        self.r2 = create_record(
            record_type=RecordType.EXPENSE, category=Category.FOOD,
            amount=Decimal('200.00'), record_date=date.today() - timedelta(days=5),
            created_by=self.admin,
        )

    def test_viewer_can_list_records(self):
        self.auth(self.viewer)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])

    def test_analyst_can_list_records(self):
        self.auth(self.analyst)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_list_records(self):
        self.unauth()
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filter_by_record_type(self):
        self.auth(self.viewer)
        res = self.client.get(self.url + '?record_type=income')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for record in res.data['results']:
            self.assertEqual(record['record_type'], 'income')

    def test_filter_by_category(self):
        self.auth(self.viewer)
        res = self.client.get(self.url + '?category=food')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for record in res.data['results']:
            self.assertEqual(record['category'], 'food')

    def test_filter_by_date_range(self):
        self.auth(self.viewer)
        today = date.today().isoformat()
        res = self.client.get(self.url + f'?date_from={today}&date_to={today}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for record in res.data['results']:
            self.assertEqual(record['date'], today)

    def test_filter_by_amount_range(self):
        self.auth(self.viewer)
        res = self.client.get(self.url + '?amount_min=1000')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for record in res.data['results']:
            self.assertGreaterEqual(Decimal(record['amount']), Decimal('1000'))

    def test_search_description(self):
        self.auth(self.viewer)
        res = self.client.get(self.url + '?search=Test')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_pagination_present(self):
        self.auth(self.viewer)
        res = self.client.get(self.url)
        self.assertIn('count', res.data)
        self.assertIn('results', res.data)


class RecordCreateTests(BaseAPITest):
    url = '/api/v1/records/'

    def test_admin_can_create_income_record(self):
        self.auth(self.admin)
        res = self.client.post(self.url, {
            'record_type': 'income',
            'category': 'salary',
            'amount': '3000.00',
            'date': date.today().isoformat(),
            'description': 'Monthly salary',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['data']['record_type'], 'income')

    def test_admin_can_create_expense_record(self):
        self.auth(self.admin)
        res = self.client.post(self.url, {
            'record_type': 'expense',
            'category': 'food',
            'amount': '150.00',
            'date': date.today().isoformat(),
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_viewer_cannot_create_record(self):
        self.auth(self.viewer)
        res = self.client.post(self.url, {
            'record_type': 'income', 'category': 'salary',
            'amount': '1000.00', 'date': date.today().isoformat(),
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_analyst_cannot_create_record(self):
        self.auth(self.analyst)
        res = self.client.post(self.url, {
            'record_type': 'expense', 'category': 'food',
            'amount': '50.00', 'date': date.today().isoformat(),
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_amount_zero(self):
        self.auth(self.admin)
        res = self.client.post(self.url, {
            'record_type': 'income', 'category': 'salary',
            'amount': '0.00', 'date': date.today().isoformat(),
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_amount_negative(self):
        self.auth(self.admin)
        res = self.client.post(self.url, {
            'record_type': 'income', 'category': 'salary',
            'amount': '-100.00', 'date': date.today().isoformat(),
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_category_for_type(self):
        """Income record should not accept expense categories."""
        self.auth(self.admin)
        res = self.client.post(self.url, {
            'record_type': 'income', 'category': 'food',  # food is expense category
            'amount': '100.00', 'date': date.today().isoformat(),
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_required_fields(self):
        self.auth(self.admin)
        res = self.client.post(self.url, {'amount': '100.00'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class RecordDetailTests(BaseAPITest):

    def setUp(self):
        super().setUp()
        self.record = create_record(
            record_type=RecordType.INCOME, category=Category.SALARY,
            amount=Decimal('2000.00'), created_by=self.admin,
        )
        self.url = f'/api/v1/records/{self.record.pk}/'

    def test_viewer_can_retrieve_record(self):
        self.auth(self.viewer)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(res.data['data']['amount']), Decimal('2000.00'))

    def test_admin_can_update_record(self):
        self.auth(self.admin)
        res = self.client.patch(self.url, {'amount': '2500.00'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.record.refresh_from_db()
        self.assertEqual(self.record.amount, Decimal('2500.00'))

    def test_viewer_cannot_update_record(self):
        self.auth(self.viewer)
        res = self.client.patch(self.url, {'amount': '999.00'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_soft_deletes_record(self):
        self.auth(self.admin)
        res = self.client.delete(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.record.refresh_from_db()
        self.assertTrue(self.record.is_deleted)

    def test_soft_deleted_record_not_in_list(self):
        self.record.is_deleted = True
        self.record.save()
        self.auth(self.viewer)
        res = self.client.get('/api/v1/records/')
        ids = [r['id'] for r in res.data['results']]
        self.assertNotIn(self.record.pk, ids)

    def test_retrieve_nonexistent_record(self):
        self.auth(self.viewer)
        res = self.client.get('/api/v1/records/999999/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
