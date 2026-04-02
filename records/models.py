from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from users.models import User


class RecordType(models.TextChoices):
    INCOME = 'income', 'Income'
    EXPENSE = 'expense', 'Expense'


class Category(models.TextChoices):
    # Income categories
    SALARY = 'salary', 'Salary'
    FREELANCE = 'freelance', 'Freelance'
    INVESTMENT = 'investment', 'Investment'
    BUSINESS = 'business', 'Business'
    BONUS = 'bonus', 'Bonus'
    RENTAL = 'rental', 'Rental Income'
    OTHER_INCOME = 'other_income', 'Other Income'

    # Expense categories
    FOOD = 'food', 'Food & Dining'
    TRANSPORT = 'transport', 'Transport'
    UTILITIES = 'utilities', 'Utilities'
    HEALTHCARE = 'healthcare', 'Healthcare'
    EDUCATION = 'education', 'Education'
    ENTERTAINMENT = 'entertainment', 'Entertainment'
    SHOPPING = 'shopping', 'Shopping'
    HOUSING = 'housing', 'Housing & Rent'
    INSURANCE = 'insurance', 'Insurance'
    TAX = 'tax', 'Tax'
    OTHER_EXPENSE = 'other_expense', 'Other Expense'


class FinancialRecord(models.Model):
    # main model for storing financial entries
    # amount is always positive, record_type tells if its income or expense
    # is_deleted for soft delete so we dont lose history
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    record_type = models.CharField(
        max_length=10,
        choices=RecordType.choices,
    )
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
    )
    date = models.DateField()
    description = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')

    # Soft delete
    is_deleted = models.BooleanField(default=False)

    # Audit fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_records',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financial_records'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['record_type']),
            models.Index(fields=['category']),
            models.Index(fields=['date']),
            models.Index(fields=['is_deleted']),
        ]

    def __str__(self):
        return f"[{self.record_type.upper()}] {self.category} — {self.amount} on {self.date}"

    @property
    def signed_amount(self):
        """Returns negative amount for expenses, positive for income."""
        return self.amount if self.record_type == RecordType.INCOME else -self.amount


class ActiveRecordManager(models.Manager):
    # filters out soft deleted records automatically
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


# Attach manager
FinancialRecord.add_to_class('active', ActiveRecordManager())
