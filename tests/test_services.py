"""
Unit tests for the dashboard service layer.
These test aggregation logic directly without going through HTTP.
"""
from django.test import TestCase
from decimal import Decimal
from datetime import date, timedelta

from records.models import RecordType, Category
from dashboard import services
from .utils import create_user, create_record
from users.models import Role


class OverviewServiceTests(TestCase):

    def setUp(self):
        self.admin = create_user('admin@svc.com', role=Role.ADMIN)
        today = date.today()
        create_record(RecordType.INCOME, Category.SALARY, Decimal('4000.00'),
                      record_date=today, created_by=self.admin)
        create_record(RecordType.INCOME, Category.FREELANCE, Decimal('1000.00'),
                      record_date=today, created_by=self.admin)
        create_record(RecordType.EXPENSE, Category.FOOD, Decimal('500.00'),
                      record_date=today, created_by=self.admin)

    def test_total_income(self):
        summary = services.get_overview_summary()
        self.assertEqual(Decimal(summary['total_income']), Decimal('5000.00'))

    def test_total_expenses(self):
        summary = services.get_overview_summary()
        self.assertEqual(Decimal(summary['total_expenses']), Decimal('500.00'))

    def test_net_balance(self):
        summary = services.get_overview_summary()
        self.assertEqual(Decimal(summary['net_balance']), Decimal('4500.00'))

    def test_net_balance_status_positive(self):
        summary = services.get_overview_summary()
        self.assertEqual(summary['net_balance_status'], 'positive')

    def test_net_balance_status_negative(self):
        create_record(RecordType.EXPENSE, Category.HOUSING, Decimal('99999.00'),
                      created_by=self.admin)
        summary = services.get_overview_summary()
        self.assertEqual(summary['net_balance_status'], 'negative')

    def test_savings_rate(self):
        summary = services.get_overview_summary()
        # (4500 / 5000) * 100 = 90%
        self.assertAlmostEqual(summary['savings_rate'], 90.0, places=1)

    def test_date_range_filter(self):
        future = date.today() + timedelta(days=30)
        create_record(RecordType.INCOME, Category.BONUS, Decimal('2000.00'),
                      record_date=future, created_by=self.admin)
        today = date.today()
        summary = services.get_overview_summary(date_from=today, date_to=today)
        self.assertEqual(Decimal(summary['total_income']), Decimal('5000.00'))

    def test_empty_result_when_no_records(self):
        from records.models import FinancialRecord
        FinancialRecord.objects.all().delete()
        summary = services.get_overview_summary()
        self.assertEqual(Decimal(summary['total_income']), Decimal('0.00'))
        self.assertEqual(Decimal(summary['total_expenses']), Decimal('0.00'))
        self.assertEqual(summary['savings_rate'], 0.0)

    def test_record_counts(self):
        summary = services.get_overview_summary()
        self.assertEqual(summary['income_count'], 2)
        self.assertEqual(summary['expense_count'], 1)
        self.assertEqual(summary['total_records'], 3)


class CategoryBreakdownServiceTests(TestCase):

    def setUp(self):
        self.admin = create_user('admin@cat.com', role=Role.ADMIN)
        create_record(RecordType.EXPENSE, Category.FOOD, Decimal('300.00'), created_by=self.admin)
        create_record(RecordType.EXPENSE, Category.FOOD, Decimal('200.00'), created_by=self.admin)
        create_record(RecordType.EXPENSE, Category.TRANSPORT, Decimal('100.00'), created_by=self.admin)
        create_record(RecordType.INCOME, Category.SALARY, Decimal('3000.00'), created_by=self.admin)

    def test_expense_category_totals(self):
        breakdown = services.get_category_breakdown(record_type='expense')
        categories = {item['category']: Decimal(item['total']) for item in breakdown}
        self.assertEqual(categories['food'], Decimal('500.00'))
        self.assertEqual(categories['transport'], Decimal('100.00'))

    def test_income_only_filter(self):
        breakdown = services.get_category_breakdown(record_type='income')
        self.assertEqual(len(breakdown), 1)
        self.assertEqual(breakdown[0]['category'], 'salary')

    def test_percentage_calculation(self):
        breakdown = services.get_category_breakdown(record_type='expense')
        # food = 500 / 600 = 83.33%
        food_item = next(b for b in breakdown if b['category'] == 'food')
        self.assertAlmostEqual(food_item['percentage'], 83.33, places=1)


class RecentActivityServiceTests(TestCase):

    def setUp(self):
        self.admin = create_user('admin@rec.com', role=Role.ADMIN)
        for i in range(15):
            create_record(
                RecordType.INCOME, Category.SALARY,
                Decimal('100.00'),
                record_date=date.today() - timedelta(days=i),
                created_by=self.admin,
            )

    def test_default_limit_10(self):
        activity = services.get_recent_activity()
        self.assertEqual(len(activity), 10)

    def test_custom_limit(self):
        activity = services.get_recent_activity(limit=5)
        self.assertEqual(len(activity), 5)

    def test_ordered_most_recent_first(self):
        activity = services.get_recent_activity(limit=15)
        dates = [item['date'] for item in activity]
        self.assertEqual(dates, sorted(dates, reverse=True))


class SoftDeleteServiceTests(TestCase):
    """Ensure soft-deleted records are excluded from all service queries."""

    def setUp(self):
        self.admin = create_user('admin@soft.com', role=Role.ADMIN)
        self.live = create_record(RecordType.INCOME, Category.SALARY,
                                  Decimal('1000.00'), created_by=self.admin)
        self.deleted = create_record(RecordType.INCOME, Category.BONUS,
                                     Decimal('9999.00'), created_by=self.admin,
                                     is_deleted=True)

    def test_deleted_excluded_from_summary(self):
        summary = services.get_overview_summary()
        self.assertEqual(Decimal(summary['total_income']), Decimal('1000.00'))

    def test_deleted_excluded_from_recent_activity(self):
        activity = services.get_recent_activity(limit=50)
        ids = [a['id'] for a in activity]
        self.assertNotIn(self.deleted.pk, ids)

    def test_deleted_excluded_from_category_breakdown(self):
        breakdown = services.get_category_breakdown(record_type='income')
        categories = [b['category'] for b in breakdown]
        self.assertNotIn('bonus', categories)
