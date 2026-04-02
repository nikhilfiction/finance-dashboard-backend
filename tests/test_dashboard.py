from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta

from records.models import RecordType, Category
from .utils import BaseAPITest, create_record


class DashboardSetupMixin:
    """Mixin that seeds a few records for dashboard tests."""

    def seed_records(self):
        today = date.today()
        create_record(RecordType.INCOME, Category.SALARY, Decimal('5000.00'),
                      record_date=today, created_by=self.admin)
        create_record(RecordType.INCOME, Category.FREELANCE, Decimal('1500.00'),
                      record_date=today - timedelta(days=10), created_by=self.admin)
        create_record(RecordType.EXPENSE, Category.FOOD, Decimal('300.00'),
                      record_date=today, created_by=self.admin)
        create_record(RecordType.EXPENSE, Category.TRANSPORT, Decimal('150.00'),
                      record_date=today - timedelta(days=3), created_by=self.admin)
        create_record(RecordType.EXPENSE, Category.UTILITIES, Decimal('200.00'),
                      record_date=today - timedelta(days=15), created_by=self.admin)


class OverviewSummaryTests(DashboardSetupMixin, BaseAPITest):
    url = '/api/v1/dashboard/summary/'

    def setUp(self):
        super().setUp()
        self.seed_records()

    def test_viewer_can_access_summary(self):
        self.auth(self.viewer)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])

    def test_analyst_can_access_summary(self):
        self.auth(self.analyst)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_can_access_summary(self):
        self.auth(self.admin)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        self.unauth()
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_summary_totals_correct(self):
        self.auth(self.admin)
        res = self.client.get(self.url)
        data = res.data['data']
        self.assertEqual(Decimal(data['total_income']), Decimal('6500.00'))
        self.assertEqual(Decimal(data['total_expenses']), Decimal('650.00'))
        self.assertEqual(Decimal(data['net_balance']), Decimal('5850.00'))
        self.assertEqual(data['net_balance_status'], 'positive')

    def test_summary_with_date_filter(self):
        self.auth(self.admin)
        today = date.today().isoformat()
        res = self.client.get(self.url + f'?date_from={today}&date_to={today}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data['data']
        # Only records from today
        self.assertEqual(Decimal(data['total_income']), Decimal('5000.00'))
        self.assertEqual(Decimal(data['total_expenses']), Decimal('300.00'))

    def test_summary_with_invalid_date(self):
        self.auth(self.admin)
        res = self.client.get(self.url + '?date_from=not-a-date')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_savings_rate_calculated(self):
        self.auth(self.admin)
        res = self.client.get(self.url)
        data = res.data['data']
        self.assertIn('savings_rate', data)
        self.assertGreater(data['savings_rate'], 0)


class CurrentMonthSnapshotTests(DashboardSetupMixin, BaseAPITest):
    url = '/api/v1/dashboard/snapshot/'

    def setUp(self):
        super().setUp()
        self.seed_records()

    def test_viewer_can_access_snapshot(self):
        self.auth(self.viewer)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('total_income', res.data['data'])

    def test_unauthenticated_denied(self):
        self.unauth()
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class CategoryBreakdownTests(DashboardSetupMixin, BaseAPITest):
    url = '/api/v1/dashboard/categories/'

    def setUp(self):
        super().setUp()
        self.seed_records()

    def test_analyst_can_access(self):
        self.auth(self.analyst)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_can_access(self):
        self.auth(self.admin)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_denied(self):
        self.auth(self.viewer)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_by_expense(self):
        self.auth(self.analyst)
        res = self.client.get(self.url + '?record_type=expense')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for item in res.data['data']:
            self.assertEqual(item['record_type'], 'expense')

    def test_filter_by_income(self):
        self.auth(self.analyst)
        res = self.client.get(self.url + '?record_type=income')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for item in res.data['data']:
            self.assertEqual(item['record_type'], 'income')

    def test_invalid_record_type(self):
        self.auth(self.analyst)
        res = self.client.get(self.url + '?record_type=invalid')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_percentage_sums_to_100(self):
        self.auth(self.admin)
        res = self.client.get(self.url + '?record_type=expense')
        percentages = [item['percentage'] for item in res.data['data']]
        self.assertAlmostEqual(sum(percentages), 100.0, places=0)


class MonthlyTrendsTests(DashboardSetupMixin, BaseAPITest):
    url = '/api/v1/dashboard/trends/monthly/'

    def setUp(self):
        super().setUp()
        self.seed_records()

    def test_analyst_can_access(self):
        self.auth(self.analyst)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_denied(self):
        self.auth(self.viewer)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_response_structure(self):
        self.auth(self.analyst)
        res = self.client.get(self.url)
        self.assertIn('data', res.data)
        if res.data['data']:
            item = res.data['data'][0]
            self.assertIn('month', item)
            self.assertIn('total_income', item)
            self.assertIn('total_expenses', item)
            self.assertIn('net', item)

    def test_filter_by_year(self):
        self.auth(self.analyst)
        year = date.today().year
        res = self.client.get(self.url + f'?year={year}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for item in res.data['data']:
            self.assertTrue(item['month'].startswith(str(year)))

    def test_invalid_year(self):
        self.auth(self.analyst)
        res = self.client.get(self.url + '?year=notayear')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_months_out_of_range(self):
        self.auth(self.analyst)
        res = self.client.get(self.url + '?months=999')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class WeeklyTrendsTests(DashboardSetupMixin, BaseAPITest):
    url = '/api/v1/dashboard/trends/weekly/'

    def setUp(self):
        super().setUp()
        self.seed_records()

    def test_analyst_can_access(self):
        self.auth(self.analyst)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_denied(self):
        self.auth(self.viewer)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_custom_weeks_param(self):
        self.auth(self.analyst)
        res = self.client.get(self.url + '?weeks=4')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_invalid_weeks(self):
        self.auth(self.analyst)
        res = self.client.get(self.url + '?weeks=100')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class RecentActivityTests(DashboardSetupMixin, BaseAPITest):
    url = '/api/v1/dashboard/recent/'

    def setUp(self):
        super().setUp()
        self.seed_records()

    def test_viewer_can_access(self):
        self.auth(self.viewer)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('data', res.data)

    def test_default_limit_is_10(self):
        self.auth(self.viewer)
        res = self.client.get(self.url)
        self.assertLessEqual(len(res.data['data']), 10)

    def test_custom_limit(self):
        self.auth(self.viewer)
        res = self.client.get(self.url + '?limit=3')
        self.assertLessEqual(len(res.data['data']), 3)

    def test_limit_too_large(self):
        self.auth(self.viewer)
        res = self.client.get(self.url + '?limit=999')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class TopSpendingTests(DashboardSetupMixin, BaseAPITest):
    url = '/api/v1/dashboard/top-spending/'

    def setUp(self):
        super().setUp()
        self.seed_records()

    def test_analyst_can_access(self):
        self.auth(self.analyst)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_denied(self):
        self.auth(self.viewer)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_results_are_ranked(self):
        self.auth(self.admin)
        res = self.client.get(self.url)
        data = res.data['data']
        ranks = [item['rank'] for item in data]
        self.assertEqual(ranks, list(range(1, len(ranks) + 1)))

    def test_results_ordered_by_total_desc(self):
        self.auth(self.admin)
        res = self.client.get(self.url)
        totals = [Decimal(item['total']) for item in res.data['data']]
        self.assertEqual(totals, sorted(totals, reverse=True))

    def test_custom_limit(self):
        self.auth(self.admin)
        res = self.client.get(self.url + '?limit=2')
        self.assertLessEqual(len(res.data['data']), 2)

    def test_date_filtered_top_spending(self):
        self.auth(self.admin)
        today = date.today().isoformat()
        res = self.client.get(self.url + f'?date_from={today}&date_to={today}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
