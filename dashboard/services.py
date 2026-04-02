# all dashboard aggregation logic lives here
# keeping it separate from views makes it easier to test

from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncMonth, TruncWeek, TruncDate
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

from records.models import FinancialRecord, RecordType


def _base_qs():
    """Return the base queryset of non-deleted records."""
    return FinancialRecord.active.all()


def _filter_by_date(qs, date_from=None, date_to=None):
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)
    return qs


# ---------------------------------------------------------------------------
# 1. Overview Summary
# ---------------------------------------------------------------------------

def get_overview_summary(date_from=None, date_to=None):
    # returns totals for income, expenses and net balance
    # optional date range filter
    qs = _filter_by_date(_base_qs(), date_from, date_to)

    totals = qs.aggregate(
        total_income=Sum('amount', filter=Q(record_type=RecordType.INCOME)),
        total_expenses=Sum('amount', filter=Q(record_type=RecordType.EXPENSE)),
        income_count=Count('id', filter=Q(record_type=RecordType.INCOME)),
        expense_count=Count('id', filter=Q(record_type=RecordType.EXPENSE)),
        total_count=Count('id'),
    )

    total_income = totals['total_income'] or Decimal('0.00')
    total_expenses = totals['total_expenses'] or Decimal('0.00')
    net_balance = total_income - total_expenses

    return {
        "total_income": str(total_income),
        "total_expenses": str(total_expenses),
        "net_balance": str(net_balance),
        "net_balance_status": "positive" if net_balance >= 0 else "negative",
        "total_records": totals['total_count'],
        "income_count": totals['income_count'],
        "expense_count": totals['expense_count'],
        "savings_rate": (
            round((float(net_balance) / float(total_income)) * 100, 2)
            if total_income > 0 else 0.0
        ),
    }


# ---------------------------------------------------------------------------
# 2. Category-wise Totals
# ---------------------------------------------------------------------------

def get_category_breakdown(record_type=None, date_from=None, date_to=None):
    # groups records by category and calculates totals + percentage share
    qs = _filter_by_date(_base_qs(), date_from, date_to)
    if record_type:
        qs = qs.filter(record_type=record_type)

    rows = (
        qs.values('category', 'record_type')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )

    # Calculate grand total for percentage share
    grand_total = sum(r['total'] for r in rows) or Decimal('1')

    return [
        {
            "category": r['category'],
            "record_type": r['record_type'],
            "total": str(r['total']),
            "count": r['count'],
            "percentage": round(float(r['total']) / float(grand_total) * 100, 2),
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# 3. Monthly Trends
# ---------------------------------------------------------------------------

def get_monthly_trends(year=None, months=12):
    # income vs expenses per month, defaults to last 12 months
    qs = _base_qs()

    if year:
        qs = qs.filter(date__year=year)
    else:
        cutoff = date.today().replace(day=1) - timedelta(days=30 * (months - 1))
        qs = qs.filter(date__gte=cutoff)

    rows = (
        qs.annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(
            total_income=Sum('amount', filter=Q(record_type=RecordType.INCOME)),
            total_expenses=Sum('amount', filter=Q(record_type=RecordType.EXPENSE)),
            income_count=Count('id', filter=Q(record_type=RecordType.INCOME)),
            expense_count=Count('id', filter=Q(record_type=RecordType.EXPENSE)),
        )
        .order_by('month')
    )

    return [
        {
            "month": r['month'].strftime('%Y-%m'),
            "total_income": str(r['total_income'] or Decimal('0.00')),
            "total_expenses": str(r['total_expenses'] or Decimal('0.00')),
            "net": str(
                (r['total_income'] or Decimal('0.00')) -
                (r['total_expenses'] or Decimal('0.00'))
            ),
            "income_count": r['income_count'],
            "expense_count": r['expense_count'],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# 4. Weekly Trends
# ---------------------------------------------------------------------------

def get_weekly_trends(weeks=8):
    # same as monthly but grouped by week
    cutoff = date.today() - timedelta(weeks=weeks)
    qs = _base_qs().filter(date__gte=cutoff)

    rows = (
        qs.annotate(week=TruncWeek('date'))
        .values('week')
        .annotate(
            total_income=Sum('amount', filter=Q(record_type=RecordType.INCOME)),
            total_expenses=Sum('amount', filter=Q(record_type=RecordType.EXPENSE)),
        )
        .order_by('week')
    )

    return [
        {
            "week_start": r['week'].strftime('%Y-%m-%d'),
            "total_income": str(r['total_income'] or Decimal('0.00')),
            "total_expenses": str(r['total_expenses'] or Decimal('0.00')),
            "net": str(
                (r['total_income'] or Decimal('0.00')) -
                (r['total_expenses'] or Decimal('0.00'))
            ),
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# 5. Recent Activity
# ---------------------------------------------------------------------------

def get_recent_activity(limit=10):
    # just returns the most recent N records
    records = (
        _base_qs()
        .select_related('created_by')
        .order_by('-date', '-created_at')[:limit]
    )
    return [
        {
            "id": r.id,
            "record_type": r.record_type,
            "category": r.category,
            "amount": str(r.amount),
            "date": str(r.date),
            "description": r.description,
            "created_by": r.created_by.get_full_name() if r.created_by else None,
        }
        for r in records
    ]


# ---------------------------------------------------------------------------
# 6. Current Month Snapshot (for Viewer role)
# ---------------------------------------------------------------------------

def get_current_month_snapshot():
    # quick summary for just the current month
    today = date.today()
    return get_overview_summary(
        date_from=today.replace(day=1),
        date_to=today,
    )


# ---------------------------------------------------------------------------
# 7. Top Spending Categories
# ---------------------------------------------------------------------------

def get_top_spending_categories(limit=5, date_from=None, date_to=None):
    # top N expense categories ranked by total amount spent
    qs = _filter_by_date(_base_qs(), date_from, date_to)
    qs = qs.filter(record_type=RecordType.EXPENSE)

    rows = (
        qs.values('category')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')[:limit]
    )

    grand_total = sum(r['total'] for r in rows) or Decimal('1')
    return [
        {
            "rank": idx + 1,
            "category": r['category'],
            "total": str(r['total']),
            "count": r['count'],
            "percentage": round(float(r['total']) / float(grand_total) * 100, 2),
        }
        for idx, r in enumerate(rows)
    ]
