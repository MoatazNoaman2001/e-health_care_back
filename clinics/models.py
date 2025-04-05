from django.db import models
from django.utils.translation import gettext_lazy as _
from common.models import TimeStampedModel
from common.validators import validate_phone_number
from doctors.models import Doctor


class Clinic(TimeStampedModel):
    """
    Model representing a clinic or healthcare facility.
    """

    class ClinicType(models.TextChoices):
        HOSPITAL = 'hospital', _('Hospital')
        CLINIC = 'clinic', _('Clinic')
        LABORATORY = 'laboratory', _('Laboratory')
        PHARMACY = 'pharmacy', _('Pharmacy')
        IMAGING_CENTER = 'imaging_center', _('Imaging Center')
        SPECIALTY_CENTER = 'specialty_center', _('Specialty Center')
        OTHER = 'other', _('Other')

    name = models.CharField(max_length=255)
    clinic_type = models.CharField(max_length=20, choices=ClinicType.choices, default=ClinicType.CLINIC)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="United States")
    phone_number = models.CharField(max_length=20, validators=[validate_phone_number])
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    services = models.TextField(blank=True, null=True)
    facilities = models.TextField(blank=True, null=True)
    established_year = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    logo = models.ImageField(upload_to='clinic_logos/', null=True, blank=True)
    featured_image = models.ImageField(upload_to='clinic_images/', null=True, blank=True)

    def __str__(self):
        return self.name


class ClinicGallery(TimeStampedModel):
    """
    Model for storing clinic gallery images.
    """
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='clinic_gallery/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Clinic Gallery")
        verbose_name_plural = _("Clinic Galleries")

    def __str__(self):
        return f"{self.clinic.name} Gallery Image {self.id}"


class DoctorClinic(TimeStampedModel):
    """
    Model for linking doctors to clinics.
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='clinics')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='doctors')
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ('doctor', 'clinic')
        verbose_name = _("Doctor Clinic")
        verbose_name_plural = _("Doctor Clinics")

    def __str__(self):
        return f"{self.doctor} at {self.clinic}"

    def save(self, *args, **kwargs):
        """
        Ensure only one clinic is marked as primary for a doctor.
        """
        if self.is_primary:
            # Set all other clinics of this doctor to not primary
            DoctorClinic.objects.filter(
                doctor=self.doctor,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class ClinicBusinessHours(TimeStampedModel):
    """
    Model for clinic business hours.
    """

    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, _('Monday')
        TUESDAY = 1, _('Tuesday')
        WEDNESDAY = 2, _('Wednesday')
        THURSDAY = 3, _('Thursday')
        FRIDAY = 4, _('Friday')
        SATURDAY = 5, _('Saturday')
        SUNDAY = 6, _('Sunday')

    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='business_hours')
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('clinic', 'day_of_week')
        verbose_name = _("Clinic Business Hours")
        verbose_name_plural = _("Clinic Business Hours")
        ordering = ['day_of_week']

    def __str__(self):
        if self.is_closed:
            return f"{self.clinic.name} - {self.get_day_of_week_display()} - Closed"
        return f"{self.clinic.name} - {self.get_day_of_week_display()} - {self.opening_time.strftime('%H:%M')} to {self.closing_time.strftime('%H:%M')}"


class ClinicSpecialty(TimeStampedModel):
    """
    Model for clinic specialties.
    """
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='specialties')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('clinic', 'name')
        verbose_name = _("Clinic Specialty")
        verbose_name_plural = _("Clinic Specialties")

    def __str__(self):
        return f"{self.clinic.name} - {self.name}"


class ClinicInsurance(TimeStampedModel):
    """
    Model for accepted insurance providers at a clinic.
    """
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='accepted_insurances')
    insurance = models.ForeignKey('doctors.InsuranceProvider', on_delete=models.CASCADE, related_name='clinics')

    class Meta:
        unique_together = ('clinic', 'insurance')
        verbose_name = _("Clinic Insurance")
        verbose_name_plural = _("Clinic Insurances")

    def __str__(self):
        return f"{self.clinic.name} - {self.insurance.name}"


class ClinicReview(TimeStampedModel):
    """
    Model for clinic reviews.
    """
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='clinic_reviews')
    rating = models.PositiveSmallIntegerField(
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        help_text=_('Rating from 1 to 5')
    )
    title = models.CharField(max_length=100, blank=True, null=True)
    review = models.TextField()
    is_verified = models.BooleanField(default=False)

    class Meta:
        unique_together = ('clinic', 'user')
        verbose_name = _("Clinic Review")
        verbose_name_plural = _("Clinic Reviews")

    def __str__(self):
        return f"{self.clinic.name} - {self.rating} star review by {self.user.email}"