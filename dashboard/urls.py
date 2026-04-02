from django.urls import path
from .views import (
    OverviewSummaryView,
    CurrentMonthSnapshotView,
    CategoryBreakdownView,
    MonthlyTrendsView,
    WeeklyTrendsView,
    RecentActivityView,
    TopSpendingCategoriesView,
)

urlpatterns = [
    # All authenticated roles
    path('summary/', OverviewSummaryView.as_view(), name='dashboard-summary'),
    path('snapshot/', CurrentMonthSnapshotView.as_view(), name='dashboard-snapshot'),
    path('recent/', RecentActivityView.as_view(), name='dashboard-recent'),

    # Analyst + Admin only
    path('categories/', CategoryBreakdownView.as_view(), name='dashboard-categories'),
    path('trends/monthly/', MonthlyTrendsView.as_view(), name='dashboard-monthly-trends'),
    path('trends/weekly/', WeeklyTrendsView.as_view(), name='dashboard-weekly-trends'),
    path('top-spending/', TopSpendingCategoriesView.as_view(), name='dashboard-top-spending'),
]
