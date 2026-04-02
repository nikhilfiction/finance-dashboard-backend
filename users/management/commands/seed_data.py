import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from users.models import User, Role
from records.models import FinancialRecord, RecordType, Category


SAMPLE_RECORDS = [
    # (type, category, amount, description)
    (RecordType.INCOME, Category.SALARY, Decimal('45000.00'), 'Monthly salary'),
    (RecordType.INCOME, Category.SALARY, Decimal('45000.00'), 'Monthly salary'),
    (RecordType.INCOME, Category.SALARY, Decimal('47000.00'), 'Salary after appraisal'),
    (RecordType.INCOME, Category.FREELANCE, Decimal('12000.00'), 'React dashboard project'),
    (RecordType.INCOME, Category.FREELANCE, Decimal('8500.00'), 'API integration work'),
    (RecordType.INCOME, Category.INVESTMENT, Decimal('3200.00'), 'Mutual fund returns'),
    (RecordType.INCOME, Category.BONUS, Decimal('15000.00'), 'Diwali bonus'),
    (RecordType.INCOME, Category.RENTAL, Decimal('9000.00'), 'PG room rent received'),
    (RecordType.INCOME, Category.FREELANCE, Decimal('6000.00'), 'Logo design work'),
    (RecordType.INCOME, Category.OTHER_INCOME, Decimal('2500.00'), 'Referral bonus from Swiggy'),
    (RecordType.EXPENSE, Category.HOUSING, Decimal('12000.00'), 'Room rent - Koramangala'),
    (RecordType.EXPENSE, Category.HOUSING, Decimal('12000.00'), 'Room rent'),
    (RecordType.EXPENSE, Category.HOUSING, Decimal('12000.00'), 'Room rent paid'),
    (RecordType.EXPENSE, Category.FOOD, Decimal('3200.00'), 'Groceries from DMart'),
    (RecordType.EXPENSE, Category.FOOD, Decimal('1800.00'), 'Zomato and Swiggy orders'),
    (RecordType.EXPENSE, Category.FOOD, Decimal('2400.00'), 'Mess monthly fee'),
    (RecordType.EXPENSE, Category.FOOD, Decimal('900.00'), 'Tea and snacks'),
    (RecordType.EXPENSE, Category.TRANSPORT, Decimal('1500.00'), 'Ola and Uber rides'),
    (RecordType.EXPENSE, Category.TRANSPORT, Decimal('800.00'), 'Petrol for bike'),
    (RecordType.EXPENSE, Category.TRANSPORT, Decimal('1200.00'), 'Train ticket to home'),
    (RecordType.EXPENSE, Category.UTILITIES, Decimal('1100.00'), 'Electricity bill'),
    (RecordType.EXPENSE, Category.UTILITIES, Decimal('699.00'), 'Jio postpaid bill'),
    (RecordType.EXPENSE, Category.UTILITIES, Decimal('400.00'), 'Airtel broadband'),
    (RecordType.EXPENSE, Category.HEALTHCARE, Decimal('850.00'), 'Medicine from Apollo'),
    (RecordType.EXPENSE, Category.HEALTHCARE, Decimal('500.00'), 'Doctor consultation'),
    (RecordType.EXPENSE, Category.ENTERTAINMENT, Decimal('399.00'), 'Netflix subscription'),
    (RecordType.EXPENSE, Category.ENTERTAINMENT, Decimal('600.00'), 'Movie at PVR with friends'),
    (RecordType.EXPENSE, Category.SHOPPING, Decimal('2200.00'), 'Clothes from Myntra sale'),
    (RecordType.EXPENSE, Category.SHOPPING, Decimal('1500.00'), 'Earphones from Amazon'),
    (RecordType.EXPENSE, Category.EDUCATION, Decimal('2999.00'), 'Udemy course - Django REST'),
    (RecordType.EXPENSE, Category.INSURANCE, Decimal('1800.00'), 'LIC premium'),
    (RecordType.EXPENSE, Category.TAX, Decimal('5000.00'), 'Advance tax payment'),
    (RecordType.EXPENSE, Category.OTHER_EXPENSE, Decimal('750.00'), 'Birthday gift for friend'),
]


class Command(BaseCommand):
    help = 'loads sample data into the database for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='wipe existing data before seeding',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('clearing existing data...')
            FinancialRecord.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.WARNING('done.'))

        # create users
        admin, _ = User.objects.get_or_create(
            email='rahul.admin@finance.com',
            defaults={
                'first_name': 'Rahul',
                'last_name': 'Sharma',
                'role': Role.ADMIN,
                'is_staff': True,
            }
        )
        admin.set_password('Admin@1234')
        admin.save()

        analyst, _ = User.objects.get_or_create(
            email='priya.analyst@finance.com',
            defaults={
                'first_name': 'Priya',
                'last_name': 'Verma',
                'role': Role.ANALYST,
            }
        )
        analyst.set_password('Analyst@1234')
        analyst.save()

        viewer, _ = User.objects.get_or_create(
            email='arun.viewer@finance.com',
            defaults={
                'first_name': 'Arun',
                'last_name': 'Mehta',
                'role': Role.VIEWER,
            }
        )
        viewer.set_password('Viewer@1234')
        viewer.save()

        self.stdout.write(self.style.SUCCESS('created 3 users'))

        # create records spread over last 6 months
        today = date.today()
        count = 0

        for rtype, cat, amount, desc in SAMPLE_RECORDS:
            days_ago = random.randint(0, 180)
            record_date = today - timedelta(days=days_ago)

            # small variation in amounts so they dont look identical
            variation = Decimal(str(round(random.uniform(0.97, 1.03), 4)))
            final_amount = (amount * variation).quantize(Decimal('0.01'))

            FinancialRecord.objects.get_or_create(
                record_type=rtype,
                category=cat,
                amount=final_amount,
                date=record_date,
                defaults={
                    'description': desc,
                    'created_by': admin,
                }
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'created {count} financial records'))
        self.stdout.write('')
        self.stdout.write('login credentials:')
        self.stdout.write(self.style.HTTP_INFO('  Admin    → rahul.admin@finance.com    / Admin@1234'))
        self.stdout.write(self.style.HTTP_INFO('  Analyst  → priya.analyst@finance.com  / Analyst@1234'))
        self.stdout.write(self.style.HTTP_INFO('  Viewer   → arun.viewer@finance.com    / Viewer@1234'))
        self.stdout.write('')
        self.stdout.write('swagger docs → http://127.0.0.1:8000/api/docs/')
        self.stdout.write('')
