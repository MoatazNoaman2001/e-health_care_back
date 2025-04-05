from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from common.models import TimeStampedModel
from common.validators import validate_phone_number


class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    for authentication instead of username.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email field must be set'))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', User.UserType.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, TimeStampedModel):
    """
    Custom User model with email as the unique identifier.
    """

    class UserType(models.TextChoices):
        PATIENT = 'patient', _('Patient')
        DOCTOR = 'doctor', _('Doctor')
        ADMIN = 'admin', _('Admin')
        CLINIC_STAFF = 'clinic_staff', _('Clinic Staff')

    class ProfileStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        ACTIVE = 'active', _('Active')
        SUSPENDED = 'suspended', _('Suspended')
        DELETED = 'deleted', _('Deleted')

    username = None
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(
        max_length=20,
        validators=[validate_phone_number],
        blank=True,
        null=True
    )
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.PATIENT
    )
    profile_status = models.CharField(
        max_length=20,
        choices=ProfileStatus.choices,
        default=ProfileStatus.PENDING
    )
    profile_image = models.ImageField(
        upload_to='profile_images/',
        null=True,
        blank=True
    )
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    agreed_to_terms = models.BooleanField(default=False)
    registration_source = models.CharField(max_length=100, blank=True, null=True)
    two_factor_enabled = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def is_patient(self):
        """Check if user is a patient."""
        return self.user_type == self.UserType.PATIENT

    def is_doctor(self):
        """Check if user is a doctor."""
        return self.user_type == self.UserType.DOCTOR

    def is_admin(self):
        """Check if user is an admin."""
        return self.user_type == self.UserType.ADMIN

    def is_clinic_staff(self):
        """Check if user is clinic staff."""
        return self.user_type == self.UserType.CLINIC_STAFF


class EmailVerification(TimeStampedModel):
    """
    Model for storing email verification codes.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.code}"

    def is_valid(self):
        """Check if the verification code is still valid."""
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()


class PhoneVerification(TimeStampedModel):
    """
    Model for storing phone verification codes.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phone_verifications')
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.phone_number} - {self.code}"

    def is_valid(self):
        """Check if the verification code is still valid."""
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()


class UserLoginHistory(TimeStampedModel):
    """
    Model to track user login history.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    device_type = models.CharField(max_length=50, blank=True, null=True)
    login_status = models.BooleanField(default=True)  # Success or failure

    def __str__(self):
        return f"{self.user.email} - {self.created_at}"


class UserPreference(TimeStampedModel):
    """
    Model to store user preferences.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    language = models.CharField(max_length=10, default='en')
    notification_email = models.BooleanField(default=True)
    notification_sms = models.BooleanField(default=True)
    notification_push = models.BooleanField(default=True)
    theme = models.CharField(max_length=20, default='light')

    def __str__(self):
        return f"Preferences for {self.user.email}"