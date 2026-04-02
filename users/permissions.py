from rest_framework.permissions import BasePermission
from .models import Role


class IsAdmin(BasePermission):
    # only admin role gets through
    message = "Access denied. Admin role required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.role == Role.ADMIN
        )


class IsAnalystOrAdmin(BasePermission):
    # analysts and admins can access insights/analytics
    message = "Access denied. Analyst or Admin role required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.role in (Role.ANALYST, Role.ADMIN)
        )


class IsAnyAuthenticatedRole(BasePermission):
    # any logged in active user is fine here
    message = "Access denied. Authentication required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_active
        )


class IsAdminOrReadOnly(BasePermission):
    # GET requests are open to all, write operations need admin
    message = "Access denied. Admin role required for write operations."

    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False
        if request.method in self.SAFE_METHODS:
            return True
        return request.user.role == Role.ADMIN
