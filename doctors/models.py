from django.db import models
from django.utils.translation import gettext_lazy as _
from ..common.models import TimeStampedModel
from ..accounts.models import User
from ..common.validators import validate_phone_number


class Specialization(TimeStampedModel):
    """
    Medical specialization model.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Doctor(TimeStampedModel):
    """
    Model representing a doctor in the healthcare application.
    """

    class Title(models.TextChoices):
        DR = 'Dr', _('Dr.')
        PROF = 'Prof', _('Prof.')
        ASSC_PROF = 'Assc Prof', _('Associate Prof.')
        MR = 'Mr', _('Mr.')
        MRS = 'Mrs', _('Mrs.')
        MS = 'Ms', _('Ms.')

    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        PENDING = 'pending', _('Pending Verification')
        SUSPENDED = 'suspended', _('Suspended')

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    title = models.CharField(max_length=10, choices=Title.choices, default=Title.DR)
    specializations = models.ManyToManyField(Specialization, related_name='doctors')
    license_number = models.CharField(max_length=50, unique=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    bio = models.TextField(blank=True, null=True)
    education = models.TextField(blank=True, null=True)
    work_experience = models.TextField(blank=True, null=True)
    languages = models.CharField(max_length=255, blank=True, null=True, help_text=_('Comma-separated languages'))
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)
    accepts_insurance = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='doctor_profiles/', null=True, blank=True)
    video_consultation = models.BooleanField(default=False)
    home_visit = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        """Return the doctor's full name with title."""
        return f"{self.title} {self.first_name} {self.last_name}"

    @property
    def specializations_list(self):
        """Return a list of specialization names."""
        return list(self.specializations.values_list('name', flat=True))


class DoctorEducation(TimeStampedModel):
    """
    Model for doctor's educational background.
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='education_details')
    degree = models.CharField(max_length=100)
    institution = models.CharField(max_length=255)
    location = models.CharField(max_length=255, null=True, blank=True)
    start_year = models.PositiveIntegerField()
    end_year = models.PositiveIntegerField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.doctor} - {self.degree} - {self.institution}"


class DoctorWorkExperience(TimeStampedModel):
    """
    Model for doctor's work experience.
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='work_experiences')
    institution = models.CharField(max_length=255)
    position = models.CharField(max_length=100)
    location = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    start_year = models.PositiveIntegerField()
    end_year = models.PositiveIntegerField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.doctor} - {self.position} - {self.institution}"


class DoctorCertification(TimeStampedModel):
    """
    Model for doctor's certifications.
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    certificate_number = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.doctor} - {self.name}"


class InsuranceProvider(TimeStampedModel):
    """
    Model for insurance providers.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class DoctorInsurance(TimeStampedModel):
    """
    Model for linking doctors to accepted insurance providers.
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='accepted_insurances')
    insurance = models.ForeignKey(InsuranceProvider, on_delete=models.CASCADE, related_name='accepted_by_doctors')

    class Meta:
        unique_together = ('doctor', 'insurance')

    def __str__(self):
        return f"{self.doctor} - {self.insurance}"