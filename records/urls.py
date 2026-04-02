from django.urls import path
from .views import FinancialRecordListCreateView, FinancialRecordDetailView

urlpatterns = [
    path('', FinancialRecordListCreateView.as_view(), name='record-list-create'),
    path('<int:pk>/', FinancialRecordDetailView.as_view(), name='record-detail'),
]
