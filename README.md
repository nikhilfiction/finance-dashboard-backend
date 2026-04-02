# Finance Dashboard Backend

This is a backend project I built for managing financial records with role-based access. Different users get different levels of access depending on their role. Built using Django and Django REST Framework.

---

## What this project does

- Users can register and login using JWT tokens
- There are 3 roles: Viewer, Analyst, and Admin - each with different permissions
- Admins can create, update and delete financial records
- Everyone can view records and basic dashboard stats
- Analysts and Admins get access to detailed analytics like trends and category breakdowns
- All list endpoints have pagination, filtering and search support

---

## Tech I used

- Python + Django 5.0
- Django REST Framework
- SQLite (simple, no setup needed)
- JWT auth via `djangorestframework-simplejwt`
- `django-filter` for filtering
- `drf-spectacular` for auto API docs (Swagger)

---

## Project Structure

```
finance_backend/
├── finance_backend/       # main django config
│   ├── settings.py
│   ├── urls.py
│   └── exceptions.py      # custom error responses
│
├── users/                 # handles auth + user management
│   ├── models.py          # custom user model with roles
│   ├── permissions.py     # role permission classes
│   ├── serializers.py
│   ├── views/
│   │   ├── auth_views.py  # register, login, logout, me
│   │   └── user_views.py  # admin user management
│   └── urls/
│
├── records/               # financial records CRUD
│   ├── models.py
│   ├── serializers.py
│   ├── filters.py
│   └── views.py
│
├── dashboard/             # analytics and summary APIs
│   ├── services.py        # all the aggregation logic
│   └── views.py
│
├── tests/                 # test cases
│   ├── test_users.py
│   ├── test_records.py
│   ├── test_dashboard.py
│   ├── test_services.py
│   └── test_permissions.py
│
├── manage.py
└── requirements.txt
```

---

## How to run this locally

**1. Clone the repo**
```bash
git clone <repo-url>
cd finance_backend
```

**2. Create and activate virtual environment**
```bash
python -m venv venv
source venv/Scripts/activate  # windows
# source venv/bin/activate    # mac/linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Make and run migrations**
```bash
python manage.py makemigrations users
python manage.py makemigrations records
python manage.py makemigrations dashboard
python manage.py migrate
```

**5. Load sample data**
```bash
python manage.py seed_data
```

**6. Start server**
```bash
python manage.py runserver
```

---

## Test users (after seeding)

| Role | Email | Password |
|------|-------|----------|
| Admin | rahul.admin@finance.com | Admin@1234 |
| Analyst | priya.analyst@finance.com | Analyst@1234 |
| Viewer | arun.viewer@finance.com | Viewer@1234 |

---

## API Docs

Once server is running, open:
- Swagger UI → http://127.0.0.1:8000/api/docs/
- ReDoc → http://127.0.0.1:8000/api/redoc/

---

## Main Endpoints

### Auth
```
POST   /api/v1/auth/register/
POST   /api/v1/auth/login/
POST   /api/v1/auth/logout/
GET    /api/v1/auth/me/
PATCH  /api/v1/auth/me/
POST   /api/v1/auth/change-password/
POST   /api/v1/auth/token/refresh/
```

### Users (admin only)
```
GET    /api/v1/users/
POST   /api/v1/users/
GET    /api/v1/users/{id}/
PATCH  /api/v1/users/{id}/
DELETE /api/v1/users/{id}/
```

### Records
```
GET    /api/v1/records/         # all roles
POST   /api/v1/records/         # admin only
GET    /api/v1/records/{id}/    # all roles
PATCH  /api/v1/records/{id}/    # admin only
DELETE /api/v1/records/{id}/    # admin only (soft delete)
```

### Dashboard
```
GET /api/v1/dashboard/summary/           # all roles
GET /api/v1/dashboard/snapshot/          # all roles
GET /api/v1/dashboard/recent/            # all roles
GET /api/v1/dashboard/categories/        # analyst + admin
GET /api/v1/dashboard/trends/monthly/    # analyst + admin
GET /api/v1/dashboard/trends/weekly/     # analyst + admin
GET /api/v1/dashboard/top-spending/      # analyst + admin
```

---

## Who can do what

| Action | Viewer | Analyst | Admin |
|--------|--------|---------|-------|
| Login / Register | ✓ | ✓ | ✓ |
| View records | ✓ | ✓ | ✓ |
| Create / Edit / Delete records | ✗ | ✗ | ✓ |
| Basic dashboard (summary, recent) | ✓ | ✓ | ✓ |
| Detailed analytics (trends, categories) | ✗ | ✓ | ✓ |
| Manage users | ✗ | ✗ | ✓ |

---

## Filtering records

You can filter the records list using query params:

```
?record_type=income
?category=food
?date_from=2024-01-01&date_to=2024-12-31
?amount_min=100&amount_max=5000
?search=grocery
?ordering=-date
?page=2
```

---

## Running tests

```bash
python manage.py test tests --verbosity=2
```

---

## Some decisions I made

**Soft delete** - I didn't want to hard delete records or users since that would lose data permanently. So instead records get an `is_deleted` flag and users get `is_active=False`. They're hidden from normal queries but still in the DB.

**Amount is always positive** - Storing negative amounts felt confusing. Instead the `record_type` field (income/expense) handles the direction. There's a `signed_amount` property if you need it for calculations.

**Dashboard logic is separate** - I put all the aggregation stuff in `dashboard/services.py` as plain functions instead of mixing it into views. Made it easier to test and understand.

**Category validation** - Income records can't use expense categories and vice versa. Felt wrong to allow a "salary" marked as expense for example.

**SQLite** - Kept it simple for now. Switching to PostgreSQL later would just need a settings change, nothing else.

**Default role is Viewer** - Anyone who registers gets the lowest access level. Only admins can promote users.
