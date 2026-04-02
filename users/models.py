from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class Role(models.TextChoices):
    # 3 roles - viewer is read only, analyst gets analytics, admin gets everything
    VIEWER = 'viewer', 'Viewer'
    ANALYST = 'analyst', 'Analyst'
    ADMIN = 'admin', 'Admin'


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required.')
        email = self.normalize_email(email)
        extra_fields.setdefault('role', Role.VIEWER)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields['role'] = Role.ADMIN
        extra_fields['is_staff'] = True
        extra_fields['is_superuser'] = True
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # using email instead of username, role field controls what each user can access
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}> [{self.role}]"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    # ---- Role helpers ----
    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_analyst(self):
        return self.role == Role.ANALYST

    @property
    def is_viewer(self):
        return self.role == Role.VIEWER

    @property
    def can_manage_records(self):
        """Only admins may create, update, or delete records."""
        return self.role == Role.ADMIN

    @property
    def can_view_insights(self):
        """Analysts and admins can access detailed summary/insights."""
        return self.role in (Role.ANALYST, Role.ADMIN)
