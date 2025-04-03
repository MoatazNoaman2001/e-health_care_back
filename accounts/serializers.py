from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import User, UserPreference, EmailVerification, PhoneVerification


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    """

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number',
                  'user_type', 'profile_status', 'profile_image', 'email_verified',
                  'phone_verified', 'date_joined', 'last_login']
        read_only_fields = ['id', 'date_joined', 'last_login', 'email_verified', 'phone_verified']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    agreed_to_terms = serializers.BooleanField(required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirm_password', 'first_name', 'last_name',
                  'phone_number', 'user_type', 'agreed_to_terms']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": _("Passwords don't match.")})

        if not data.get('agreed_to_terms', False):
            raise serializers.ValidationError({"agreed_to_terms": _("You must agree to the terms and conditions.")})

        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user


class UserPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserPreference model.
    """

    class Meta:
        model = UserPreference
        fields = ['language', 'notification_email', 'notification_sms',
                  'notification_push', 'theme']


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError(_("Invalid email or password."))

        if not user.is_active:
            raise serializers.ValidationError(_("User account is disabled."))

        # Add the user to the validated data
        data['user'] = user
        return data


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    """
    old_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": _("Passwords don't match.")})
        return data

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Your old password was entered incorrectly."))
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            # We don't want to reveal that the email doesn't exist
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming a password reset.
    """
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": _("Passwords don't match.")})
        return data


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for verifying email address.
    """
    code = serializers.CharField(required=True, max_length=6, min_length=6)


class PhoneVerificationSerializer(serializers.Serializer):
    """
    Serializer for verifying phone number.
    """
    code = serializers.CharField(required=True, max_length=6, min_length=6)


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'profile_image']