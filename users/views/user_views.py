from rest_framework import generics, status, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from users.models import User
from users.permissions import IsAdmin
from users.serializers import (
    AdminUserListSerializer,
    AdminUserCreateSerializer,
    AdminUserUpdateSerializer,
    UserProfileSerializer,
)


@extend_schema(tags=['Users'])
class AdminUserListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/users/        — Admin: list all users (filterable by role, is_active)
    POST /api/v1/users/        — Admin: create a new user with a specific role
    """
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'email', 'role']
    ordering = ['-date_joined']

    def get_queryset(self):
        return User.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminUserCreateSerializer
        return AdminUserListSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AdminUserListSerializer(page, many=True)
            return self.get_paginated_response({"success": True, "data": serializer.data})
        serializer = AdminUserListSerializer(queryset, many=True)
        return Response({"success": True, "data": serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = AdminUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "success": True,
                "message": "User created successfully.",
                "data": UserProfileSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=['Users'])
class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/users/{id}/  — Admin: get a user's detail
    PATCH  /api/v1/users/{id}/  — Admin: update role or active status
    DELETE /api/v1/users/{id}/  — Admin: deactivate (soft delete) a user
    """
    permission_classes = [IsAdmin]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return AdminUserUpdateSerializer
        return UserProfileSerializer

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        return Response({"success": True, "data": UserProfileSerializer(user).data})

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        user = self.get_object()

        # Prevent admin from deactivating themselves
        if user == request.user and 'is_active' in request.data and not request.data['is_active']:
            return Response(
                {"success": False, "error": {"code": "FORBIDDEN", "message": "You cannot deactivate your own account."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "success": True,
            "message": "User updated successfully.",
            "data": UserProfileSerializer(user).data,
        })

    def destroy(self, request, *args, **kwargs):
        """Soft delete: deactivates the user instead of removing from DB."""
        user = self.get_object()
        if user == request.user:
            return Response(
                {"success": False, "error": {"code": "FORBIDDEN", "message": "You cannot delete your own account."}},
                status=status.HTTP_403_FORBIDDEN,
            )
        user.is_active = False
        user.save()
        return Response(
            {"success": True, "message": f"User '{user.email}' has been deactivated."},
            status=status.HTTP_200_OK,
        )
