from rest_framework import serializers
from .models import FinancialRecord, RecordType, Category


class FinancialRecordSerializer(serializers.ModelSerializer):
    # used for reading records, includes signed_amount and who created it
    created_by_name = serializers.SerializerMethodField()
    signed_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )

    class Meta:
        model = FinancialRecord
        fields = (
            'id',
            'amount',
            'signed_amount',
            'record_type',
            'category',
            'date',
            'description',
            'notes',
            'created_by_name',
            'created_at',
            'updated_at',
        )

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return None


class FinancialRecordCreateSerializer(serializers.ModelSerializer):
    # admin only - also checks that category matches the record type

    class Meta:
        model = FinancialRecord
        fields = ('id', 'amount', 'record_type', 'category', 'date', 'description', 'notes')
        read_only_fields = ('id',)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate(self, attrs):
        # make sure category matches record type, e.g. cant use 'food' on income
        income_categories = {
            'salary', 'freelance', 'investment', 'business',
            'bonus', 'rental', 'other_income'
        }
        expense_categories = {
            'food', 'transport', 'utilities', 'healthcare', 'education',
            'entertainment', 'shopping', 'housing', 'insurance', 'tax', 'other_expense'
        }
        record_type = attrs.get('record_type')
        category = attrs.get('category')

        if record_type == RecordType.INCOME and category not in income_categories:
            raise serializers.ValidationError({
                'category': f"Category '{category}' is not valid for income records."
            })
        if record_type == RecordType.EXPENSE and category not in expense_categories:
            raise serializers.ValidationError({
                'category': f"Category '{category}' is not valid for expense records."
            })
        return attrs

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return FinancialRecord.objects.create(**validated_data)


class FinancialRecordUpdateSerializer(serializers.ModelSerializer):
    # for editing records - record_type cant be changed after creation

    class Meta:
        model = FinancialRecord
        fields = ('amount', 'category', 'date', 'description', 'notes')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value
