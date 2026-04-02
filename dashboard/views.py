from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from users.permissions import IsAnyAuthenticatedRole, IsAnalystOrAdmin
from . import services


def _parse_date(value, param_name):
    """Parse a date string (YYYY-MM-DD). Returns None if not provided."""
    if not value:
        return None
    from datetime import date
    try:
        return date.fromisoformat(value)
    except ValueError:
        from rest_framework.exceptions import ValidationError
        raise ValidationError({param_name: "Invalid date format. Use YYYY-MM-DD."})


@extend_schema(
    tags=['Dashboard'],
    summary="Overview Summary",
    description=(
        "Returns high-level totals: total income, total expenses, net balance, "
        "savings rate, and record counts. Accessible to all authenticated users. "
        "Optional date range filter: `date_from` and `date_to` (YYYY-MM-DD)."
    ),
    parameters=[
        OpenApiParameter('date_from', OpenApiTypes.DATE, description='Start date (YYYY-MM-DD)'),
        OpenApiParameter('date_to', OpenApiTypes.DATE, description='End date (YYYY-MM-DD)'),
    ],
)
class OverviewSummaryView(APIView):
    """
    GET /api/v1/dashboard/summary/
    All authenticated roles can access this endpoint.
    """
    permission_classes = [IsAnyAuthenticatedRole]

    def get(self, request):
        date_from = _parse_date(request.query_params.get('date_from'), 'date_from')
        date_to = _parse_date(request.query_params.get('date_to'), 'date_to')
        data = services.get_overview_summary(date_from=date_from, date_to=date_to)
        return Response({"success": True, "data": data})


@extend_schema(
    tags=['Dashboard'],
    summary="Current Month Snapshot",
    description="Quick summary of income, expenses, and net balance for the current calendar month.",
)
class CurrentMonthSnapshotView(APIView):
    """
    GET /api/v1/dashboard/snapshot/
    Available to all authenticated roles.
    """
    permission_classes = [IsAnyAuthenticatedRole]

    def get(self, request):
        data = services.get_current_month_snapshot()
        return Response({"success": True, "data": data})


@extend_schema(
    tags=['Dashboard'],
    summary="Category Breakdown",
    description=(
        "Returns total amounts grouped by category with percentage share. "
        "Analyst and Admin only. "
        "Filter by `record_type` (income/expense), `date_from`, `date_to`."
    ),
    parameters=[
        OpenApiParameter('record_type', OpenApiTypes.STR, description='income or expense'),
        OpenApiParameter('date_from', OpenApiTypes.DATE, description='Start date'),
        OpenApiParameter('date_to', OpenApiTypes.DATE, description='End date'),
    ],
)
class CategoryBreakdownView(APIView):
    """
    GET /api/v1/dashboard/categories/
    Analyst and Admin only.
    """
    permission_classes = [IsAnalystOrAdmin]

    def get(self, request):
        record_type = request.query_params.get('record_type')
        date_from = _parse_date(request.query_params.get('date_from'), 'date_from')
        date_to = _parse_date(request.query_params.get('date_to'), 'date_to')

        if record_type and record_type not in ('income', 'expense'):
            return Response(
                {"success": False, "error": {"code": "BAD_REQUEST", "message": "record_type must be 'income' or 'expense'."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = services.get_category_breakdown(record_type=record_type, date_from=date_from, date_to=date_to)
        return Response({"success": True, "count": len(data), "data": data})


@extend_schema(
    tags=['Dashboard'],
    summary="Monthly Trends",
    description=(
        "Returns income vs. expenses per calendar month. "
        "Analyst and Admin only. "
        "Filter by `year` (e.g. 2024) or `months` (default: 12)."
    ),
    parameters=[
        OpenApiParameter('year', OpenApiTypes.INT, description='Filter by year (e.g. 2024)'),
        OpenApiParameter('months', OpenApiTypes.INT, description='Number of past months (default 12)'),
    ],
)
class MonthlyTrendsView(APIView):
    """
    GET /api/v1/dashboard/trends/monthly/
    Analyst and Admin only.
    """
    permission_classes = [IsAnalystOrAdmin]

    def get(self, request):
        year = request.query_params.get('year')
        months = request.query_params.get('months', 12)

        try:
            year = int(year) if year else None
            months = int(months)
            if months < 1 or months > 60:
                raise ValueError()
        except (ValueError, TypeError):
            return Response(
                {"success": False, "error": {"code": "BAD_REQUEST", "message": "Invalid year or months parameter."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = services.get_monthly_trends(year=year, months=months)
        return Response({"success": True, "count": len(data), "data": data})


@extend_schema(
    tags=['Dashboard'],
    summary="Weekly Trends",
    description=(
        "Returns income vs. expenses grouped by week. "
        "Analyst and Admin only. "
        "Filter by `weeks` (default: 8, max: 52)."
    ),
    parameters=[
        OpenApiParameter('weeks', OpenApiTypes.INT, description='Number of past weeks (default 8)'),
    ],
)
class WeeklyTrendsView(APIView):
    """
    GET /api/v1/dashboard/trends/weekly/
    Analyst and Admin only.
    """
    permission_classes = [IsAnalystOrAdmin]

    def get(self, request):
        weeks = request.query_params.get('weeks', 8)
        try:
            weeks = int(weeks)
            if weeks < 1 or weeks > 52:
                raise ValueError()
        except (ValueError, TypeError):
            return Response(
                {"success": False, "error": {"code": "BAD_REQUEST", "message": "weeks must be between 1 and 52."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = services.get_weekly_trends(weeks=weeks)
        return Response({"success": True, "count": len(data), "data": data})


@extend_schema(
    tags=['Dashboard'],
    summary="Recent Activity",
    description=(
        "Returns the most recent financial records. "
        "All authenticated roles can access this. "
        "Use `limit` param (default: 10, max: 50)."
    ),
    parameters=[
        OpenApiParameter('limit', OpenApiTypes.INT, description='Number of recent records (default 10)'),
    ],
)
class RecentActivityView(APIView):
    """
    GET /api/v1/dashboard/recent/
    All authenticated roles.
    """
    permission_classes = [IsAnyAuthenticatedRole]

    def get(self, request):
        limit = request.query_params.get('limit', 10)
        try:
            limit = int(limit)
            if limit < 1 or limit > 50:
                raise ValueError()
        except (ValueError, TypeError):
            return Response(
                {"success": False, "error": {"code": "BAD_REQUEST", "message": "limit must be between 1 and 50."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = services.get_recent_activity(limit=limit)
        return Response({"success": True, "count": len(data), "data": data})


@extend_schema(
    tags=['Dashboard'],
    summary="Top Spending Categories",
    description=(
        "Returns the top N expense categories ranked by total amount. "
        "Analyst and Admin only. "
        "Use `limit` (default: 5), `date_from`, `date_to`."
    ),
    parameters=[
        OpenApiParameter('limit', OpenApiTypes.INT, description='Number of top categories (default 5)'),
        OpenApiParameter('date_from', OpenApiTypes.DATE, description='Start date'),
        OpenApiParameter('date_to', OpenApiTypes.DATE, description='End date'),
    ],
)
class TopSpendingCategoriesView(APIView):
    """
    GET /api/v1/dashboard/top-spending/
    Analyst and Admin only.
    """
    permission_classes = [IsAnalystOrAdmin]

    def get(self, request):
        limit = request.query_params.get('limit', 5)
        date_from = _parse_date(request.query_params.get('date_from'), 'date_from')
        date_to = _parse_date(request.query_params.get('date_to'), 'date_to')

        try:
            limit = int(limit)
            if limit < 1 or limit > 20:
                raise ValueError()
        except (ValueError, TypeError):
            return Response(
                {"success": False, "error": {"code": "BAD_REQUEST", "message": "limit must be between 1 and 20."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = services.get_top_spending_categories(limit=limit, date_from=date_from, date_to=date_to)
        return Response({"success": True, "count": len(data), "data": data})
