from django.db import models
from django.utils.translation import gettext_lazy as _
from common.models import TimeStampedModel, Address
from accounts.models import User
from common.validators import validate_phone_number


class Patient(TimeStampedModel):
    """
    Model representing a patient in the healthcare application.
    """

    class Gender(models.TextChoices):
        MALE = 'male', _('Male')
        FEMALE = 'female', _('Female')
        OTHER = 'other', _('Other')
        PREFER_NOT_TO_SAY = 'prefer_not_to_say', _('Prefer not to say')

    class BloodType(models.TextChoices):
        A_POSITIVE = 'A+', _('A+')
        A_NEGATIVE = 'A-', _('A-')
        B_POSITIVE = 'B+', _('B+')
        B_NEGATIVE = 'B-', _('B-')
        AB_POSITIVE = 'AB+', _('AB+')
        AB_NEGATIVE = 'AB-', _('AB-')
        O_POSITIVE = 'O+', _('O+')
        O_NEGATIVE = 'O-', _('O-')
        UNKNOWN = 'unknown', _('Unknown')

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, choices=Gender.choices, default=Gender.PREFER_NOT_TO_SAY)
    blood_type = models.CharField(max_length=10, choices=BloodType.choices, default=BloodType.UNKNOWN)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text=_('Height in cm'))
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text=_('Weight in kg'))
    allergies = models.TextField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(
        max_length=20,
        validators=[validate_phone_number],
        blank=True,
        null=True
    )
    emergency_contact_relationship = models.CharField(max_length=50, blank=True, null=True)
    is_insured = models.BooleanField(default=False)
    insurance_provider = models.CharField(max_length=100, blank=True, null=True)
    insurance_policy_number = models.CharField(max_length=100, blank=True, null=True)
    insurance_expiry_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        """Calculate age from date of birth."""
        from django.utils import timezone
        from datetime import date

        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def full_name(self):
        """Return the patient's full name."""
        return f"{self.first_name} {self.last_name}"


class PatientAddress(TimeStampedModel, Address):
    """
    Patient address information.
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='addresses')
    is_primary = models.BooleanField(default=True)
    address_type = models.CharField(max_length=20, choices=[
        ('home', _('Home')),
        ('work', _('Work')),
        ('other', _('Other')),
    ], default='home')

    class Meta:
        verbose_name = _("Patient Address")
        verbose_name_plural = _("Patient Addresses")

    def save(self, *args, **kwargs):
        """
        Ensure only one address is marked as primary.
        """
        if self.is_primary:
            # Set all other addresses of this patient to not primary
            PatientAddress.objects.filter(
                patient=self.patient,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class MedicalHistory(TimeStampedModel):
    """
    Patient's medical history records.
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_history')
    condition = models.CharField(max_length=100)
    diagnosis_date = models.DateField()
    treatment = models.TextField(blank=True, null=True)
    is_current = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Medical History")
        verbose_name_plural = _("Medical Histories")
        ordering = ['-diagnosis_date']

    def __str__(self):
        return f"{self.patient} - {self.condition}"


class Medication(TimeStampedModel):
    """
    Patient's medication records.
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medications')
    name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    prescribing_doctor = models.CharField(max_length=100, blank=True, null=True)
    is_current = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Medication")
        verbose_name_plural = _("Medications")
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.patient} - {self.name}"


class FamilyMedicalHistory(TimeStampedModel):
    """
    Patient's family medical history.
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='family_medical_history')
    relationship = models.CharField(max_length=50)
    condition = models.CharField(max_length=100)
    age_at_diagnosis = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Family Medical History")
        verbose_name_plural = _("Family Medical Histories")

    def __str__(self):
        return f"{self.patient} - {self.relationship} - {self.condition}"