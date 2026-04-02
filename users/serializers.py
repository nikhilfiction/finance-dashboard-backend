from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Role


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Used for registering new users (public endpoint, defaults to Viewer role)."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'password', 'password_confirm')
        read_only_fields = ('id',)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """Read-only profile for the currently authenticated user."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'date_joined',
        )
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserUpdateProfileSerializer(serializers.ModelSerializer):
    """Allows a user to update their own first/last name."""
    class Meta:
        model = User
        fields = ('first_name', 'last_name')


class ChangePasswordSerializer(serializers.Serializer):
    """Allows a user to change their own password."""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password_confirm": "New passwords do not match."}
            )
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


# ---- Admin-only serializers ----

class AdminUserListSerializer(serializers.ModelSerializer):
    """Compact user list for admin panel."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'role', 'is_active', 'date_joined')

    def get_full_name(self, obj):
        return obj.get_full_name()


class AdminUserCreateSerializer(serializers.ModelSerializer):
    """Admin creates a user with a specific role."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'password')
        read_only_fields = ('id',)

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Admin can update role and active status of any user."""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'role', 'is_active')

    def validate_role(self, value):
        if value not in Role.values:
            raise serializers.ValidationError(f"Invalid role. Choices: {Role.values}")
        return value
