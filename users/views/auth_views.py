from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema

from users.models import User
from users.serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserUpdateProfileSerializer,
    ChangePasswordSerializer,
)


@extend_schema(tags=['Auth'])
class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Public endpoint — registers a new user with the default 'viewer' role.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Auto-issue tokens on registration
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "success": True,
                "message": "Registration successful.",
                "data": {
                    "user": UserProfileSerializer(user).data,
                    "tokens": {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                    },
                },
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=['Auth'])
class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    Returns JWT access and refresh tokens on valid email + password.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Attach user profile to login response
            from rest_framework_simplejwt.tokens import AccessToken
            token = AccessToken(response.data['access'])
            user = User.objects.get(id=token['user_id'])
            response.data = {
                "success": True,
                "message": "Login successful.",
                "data": {
                    "user": UserProfileSerializer(user).data,
                    "tokens": {
                        "access": response.data['access'],
                        "refresh": response.data['refresh'],
                    },
                },
            }
        return response


@extend_schema(tags=['Auth'])
class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Blacklists the refresh token, effectively logging out the user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {"success": False, "error": {"code": "BAD_REQUEST", "message": "Refresh token is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            return Response(
                {"success": False, "error": {"code": "BAD_REQUEST", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"success": True, "message": "Logged out successfully."}, status=status.HTTP_200_OK)


@extend_schema(tags=['Auth'])
class TokenRefreshView(TokenRefreshView):
    """POST /api/v1/auth/token/refresh/ — Refresh access token using refresh token."""
    pass


@extend_schema(tags=['Auth'])
class MeView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/auth/me/ — Returns the authenticated user's profile.
    PATCH /api/v1/auth/me/ — Updates first_name or last_name.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UserUpdateProfileSerializer
        return UserProfileSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        serializer = UserProfileSerializer(self.get_object())
        return Response({"success": True, "data": serializer.data})

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        instance = self.get_object()
        serializer = UserUpdateProfileSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "success": True,
            "message": "Profile updated.",
            "data": UserProfileSerializer(instance).data,
        })


@extend_schema(tags=['Auth'])
class ChangePasswordView(APIView):
    """POST /api/v1/auth/change-password/ — Allows users to change their own password."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "message": "Password changed successfully."})
