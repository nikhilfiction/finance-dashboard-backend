import django_filters
from .models import FinancialRecord, RecordType, Category


class FinancialRecordFilter(django_filters.FilterSet):
    """
    Supports rich filtering on financial records:
      - record_type      exact match (income / expense)
      - category         exact match
      - date_from        date >= value
      - date_to          date <= value
      - amount_min       amount >= value
      - amount_max       amount <= value
      - description      case-insensitive contains
    """
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    description = django_filters.CharFilter(field_name='description', lookup_expr='icontains')

    class Meta:
        model = FinancialRecord
        fields = ['record_type', 'category', 'date_from', 'date_to', 'amount_min', 'amount_max', 'description']
