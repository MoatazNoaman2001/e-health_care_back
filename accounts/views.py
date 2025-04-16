from django.utils import timezone
from django.utils.crypto import get_random_string
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import login, logout
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from common.permissions import IsOwner, IsAdmin
from common.utils import generate_random_code, get_future_date
from .models import User, UserPreference, EmailVerification, PhoneVerification
from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserPreferenceSerializer,
    LoginSerializer, PasswordChangeSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, EmailVerificationSerializer,
    PhoneVerificationSerializer, ProfileUpdateSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Custom permissions based on action.
        """
        try:
            return [permission() for permission in self.permission_classes]
        except AttributeError:
            return [IsAuthenticated()]

    def get_serializer_class(self):
        """
        Return different serializers based on the action.
        """
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action == 'update_profile':
            return ProfileUpdateSerializer
        elif self.action == 'preferences':
            return UserPreferenceSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        """
        Override create to use UserRegistrationSerializer.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create user preferences
        UserPreference.objects.create(user=user)

        # Send verification email
        self._send_verification_email(user)

        # Return the created user
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['post'],  permission_classes=[AllowAny], authentication_classes=[])
    def login(self, request):
        """
        Custom login endpoint.
        """
        print(f"permissions: ${self.get_permissions()}")

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        login(request, user)

        # Get or create token
        token, created = Token.objects.get_or_create(user=user)

        # Update last login IP
        user.last_login_ip = self._get_client_ip(request)
        user.save(update_fields=['last_login_ip'])

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Logout endpoint.
        """
        # Delete token
        Token.objects.filter(user=request.user).delete()

        # Logout from session
        logout(request)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'],  permission_classes=[AllowAny], authentication_classes=[])
    def request_password_reset(self, request):
        """
        Request a password reset.
        """
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            # Generate token
            token = default_token_generator.make_token(user)
            # Here you would typically send an email with the token
            # For the sake of this example, we'll just return the token
            return Response({
                'message': 'Password reset email sent.',
                'token': token  # In a real app, you wouldn't return this
            })
        except User.DoesNotExist:
            # We don't want to reveal that the email doesn't exist
            return Response({
                'message': 'Password reset email sent.'
            })

    @action(detail=False, methods=['post'],permission_classes=[AllowAny], authentication_classes=[])
    def reset_password_confirm(self, request):
        """
        Confirm password reset with token.
        """
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        # In a real implementation, you would check the token against a stored value
        # or use Django's token generator

        # For this example, we'll just demonstrate the concept
        # In production, you'd validate the token and find the associated user

        # Placeholder for token validation
        user_id = request.data.get('user_id')  # You'd need this value from the email link

        try:
            user = User.objects.get(id=user_id)
            # Validate token
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({'message': 'Password has been reset successfully.'})
            else:
                return Response(
                    {'error': 'Invalid token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid user.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Change password for authenticated user.
        """
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({'message': 'Password changed successfully.'})

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def send_email_verification(self, request):
        """
        Send email verification code.
        """
        self._send_verification_email(request.user)
        return Response({'message': 'Verification email sent.'})

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def verify_email(self, request):
        """
        Verify email with code.
        """
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']
        user = request.user

        # Check if code is valid
        try:
            verification = EmailVerification.objects.filter(
                user=user,
                code=code,
                is_used=False,
                expires_at__gt=timezone.now()
            ).latest('created_at')

            # Mark as verified
            user.email_verified = True
            user.save(update_fields=['email_verified'])

            # Mark code as used
            verification.is_used = True
            verification.save(update_fields=['is_used'])

            return Response({'message': 'Email verified successfully.'})
        except EmailVerification.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired verification code.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def send_phone_verification(self, request):
        """
        Send phone verification code.
        """
        user = request.user

        if not user.phone_number:
            return Response(
                {'error': 'No phone number associated with account.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate code
        code = generate_random_code()
        expires_at = get_future_date(minutes=15)

        # Save verification code
        PhoneVerification.objects.create(
            user=user,
            code=code,
            expires_at=expires_at
        )

        # Here you would typically send the code via SMS
        # For the sake of this example, we'll just return the code

        return Response({
            'message': 'Verification code sent to your phone.',
            'code': code  # In a real app, you wouldn't return this
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def verify_phone(self, request):
        """
        Verify phone with code.
        """
        serializer = PhoneVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']
        user = request.user

        # Check if code is valid
        try:
            verification = PhoneVerification.objects.filter(
                user=user,
                code=code,
                is_used=False,
                expires_at__gt=timezone.now()
            ).latest('created_at')

            # Mark as verified
            user.phone_verified = True
            user.save(update_fields=['phone_verified'])

            # Mark code as used
            verification.is_used = True
            verification.save(update_fields=['is_used'])

            return Response({'message': 'Phone verified successfully.'})
        except PhoneVerification.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired verification code.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get or update the authenticated user's profile.
        """
        user = request.user

        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data)

        serializer = ProfileUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(UserSerializer(user).data)

    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[IsAuthenticated])
    def preferences(self, request):
        """
        Get or update the authenticated user's preferences.
        """
        user = request.user
        preferences, created = UserPreference.objects.get_or_create(user=user)

        if request.method == 'GET':
            serializer = UserPreferenceSerializer(preferences)
            return Response(serializer.data)

        serializer = UserPreferenceSerializer(preferences, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def _send_verification_email(self, user):
        """
        Send an email verification code.
        """
        # Generate code
        code = generate_random_code()
        expires_at = get_future_date(minutes=30)

        # Save verification code
        EmailVerification.objects.create(
            user=user,
            code=code,
            expires_at=expires_at
        )

        # Send the verification email
        from django.core.mail import send_mail
        from config.settings.base import DEFAULT_FROM_EMAIL

        subject = "Verify your email address"
        message = f"""
            Hello {user.first_name or user.email},

            Thank you for registering. Your verification code is: {code}

            This code will expire in 30 minutes.

            Thank you,
            The Healthcare Team
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return code

    def _get_client_ip(self, request):
        """
        Get the client IP address from request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip