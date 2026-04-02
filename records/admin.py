from django.contrib import admin
from .models import FinancialRecord


@admin.register(FinancialRecord)
class FinancialRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'record_type', 'category', 'amount', 'date', 'created_by', 'is_deleted', 'created_at')
    list_filter = ('record_type', 'category', 'is_deleted')
    search_fields = ('description', 'notes')
    ordering = ('-date',)
    readonly_fields = ('created_at', 'updated_at', 'created_by')
