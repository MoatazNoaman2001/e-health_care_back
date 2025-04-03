from django.db import models
from django.utils.translation import gettext_lazy as _
from common.models import TimeStampedModel
from patients.models import Patient
from doctors.models import Doctor
from clinics.models import Clinic


class Appointment(TimeStampedModel):
    """
    Model representing a medical appointment.
    """

    class AppointmentStatus(models.TextChoices):
        SCHEDULED = 'scheduled', _('Scheduled')
        CONFIRMED = 'confirmed', _('Confirmed')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
        NO_SHOW = 'no_show', _('No Show')
        RESCHEDULED = 'rescheduled', _('Rescheduled')

    class AppointmentType(models.TextChoices):
        IN_PERSON = 'in_person', _('In Person')
        VIDEO = 'video', _('Video')
        PHONE = 'phone', _('Phone')
        HOME_VISIT = 'home_visit', _('Home Visit')

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='appointments')
    appointment_type = models.CharField(max_length=20, choices=AppointmentType.choices,
                                        default=AppointmentType.IN_PERSON)
    status = models.CharField(max_length=20, choices=AppointmentStatus.choices, default=AppointmentStatus.SCHEDULED)
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration = models.PositiveIntegerField(default=30, help_text=_('Duration in minutes'))
    reason = models.TextField()
    notes = models.TextField(blank=True, null=True)
    is_first_visit = models.BooleanField(default=False)
    is_follow_up = models.BooleanField(default=False)
    is_emergency = models.BooleanField(default=False)
    chief_complaint = models.CharField(max_length=255, blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    cancelled_by = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('patient', _('Patient')),
        ('doctor', _('Doctor')),
        ('clinic', _('Clinic')),
        ('system', _('System')),
    ])
    cancelled_at = models.DateTimeField(blank=True, null=True)
    reminder_sent = models.BooleanField(default=False)
    followup_date = models.DateField(blank=True, null=True)
    insurance_verified = models.BooleanField(default=False)
    payment_status = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('pending', _('Pending')),
        ('paid', _('Paid')),
        ('insurance', _('Insurance')),
        ('waived', _('Waived')),
    ])

    class Meta:
        verbose_name = _('Appointment')
        verbose_name_plural = _('Appointments')
        ordering = ['-scheduled_date', '-scheduled_time']

    def __str__(self):
        return f"{self.patient} with {self.doctor} on {self.scheduled_date} at {self.scheduled_time}"

    @property
    def is_past(self):
        """Check if the appointment date is in the past."""
        from django.utils import timezone
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(self.scheduled_date, self.scheduled_time)
        )
        return appointment_datetime < timezone.now()

    @property
    def is_today(self):
        """Check if the appointment is scheduled for today."""
        from django.utils import timezone
        return self.scheduled_date == timezone.now().date()

    @property
    def formatted_time(self):
        """Return the appointment time in a user-friendly format."""
        return self.scheduled_time.strftime('%I:%M %p')

    @property
    def end_time(self):
        """Calculate and return the appointment end time."""
        from datetime import timedelta
        start_datetime = timezone.datetime.combine(
            self.scheduled_date, self.scheduled_time
        )
        end_datetime = start_datetime + timedelta(minutes=self.duration)
        return end_datetime.time()


class AppointmentDocument(TimeStampedModel):
    """
    Model for documents related to an appointment.
    """
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='appointment_documents/')
    document_type = models.CharField(max_length=50, choices=[
        ('prescription', _('Prescription')),
        ('lab_results', _('Lab Results')),
        ('medical_certificate', _('Medical Certificate')),
        ('referral', _('Referral')),
        ('other', _('Other')),
    ])
    notes = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True,
                                    related_name='uploaded_documents')

    class Meta:
        verbose_name = _('Appointment Document')
        verbose_name_plural = _('Appointment Documents')

    def __str__(self):
        return f"{self.title} for {self.appointment}"


class MedicalRecord(TimeStampedModel):
    """
    Model for storing medical records related to an appointment.
    """
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='medical_record')
    vital_signs = models.JSONField(default=dict, blank=True,
                                   help_text=_('Blood pressure, heart rate, temperature, etc.'))
    symptoms = models.TextField(blank=True, null=True)
    diagnosis = models.TextField(blank=True, null=True)
    treatment_plan = models.TextField(blank=True, null=True)
    prescription = models.TextField(blank=True, null=True)
    lab_orders = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    followup_instructions = models.TextField(blank=True, null=True)
    doctor_signature = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Medical Record')
        verbose_name_plural = _('Medical Records')

    def __str__(self):
        return f"Medical Record for {self.appointment}"


class AppointmentReminder(TimeStampedModel):
    """
    Model for tracking appointment reminders.
    """
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=[
        ('email', _('Email')),
        ('sms', _('SMS')),
        ('push', _('Push Notification')),
    ])
    scheduled_time = models.DateTimeField()
    sent_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', _('Pending')),
        ('sent', _('Sent')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    ], default='pending')
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _('Appointment Reminder')
        verbose_name_plural = _('Appointment Reminders')

    def __str__(self):
        return f"{self.get_reminder_type_display()} reminder for {self.appointment}"


class AppointmentFeedback(TimeStampedModel):
    """
    Model for patient feedback about an appointment.
    """
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='feedback')
    rating = models.PositiveSmallIntegerField(
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        help_text=_('Rating from 1 to 5')
    )
    comments = models.TextField(blank=True, null=True)
    doctor_punctuality = models.PositiveSmallIntegerField(
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        help_text=_('Rating from 1 to 5'),
        blank=True, null=True
    )
    facility_cleanliness = models.PositiveSmallIntegerField(
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        help_text=_('Rating from 1 to 5'),
        blank=True, null=True
    )
    staff_friendliness = models.PositiveSmallIntegerField(
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        help_text=_('Rating from 1 to 5'),
        blank=True, null=True
    )
    wait_time = models.PositiveSmallIntegerField(
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        help_text=_('Rating from 1 to 5'),
        blank=True, null=True
    )
    would_recommend = models.BooleanField(blank=True, null=True)

    class Meta:
        verbose_name = _('Appointment Feedback')
        verbose_name_plural = _('Appointment Feedback')

    def __str__(self):
        return f"Feedback for {self.appointment}"