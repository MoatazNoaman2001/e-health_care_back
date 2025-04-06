from django.db import models
from django.utils.translation import gettext_lazy as _
from common.models import TimeStampedModel
from doctors.models import Doctor
from clinics.models import Clinic


class Schedule(TimeStampedModel):
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, _('Monday')
        TUESDAY = 1, _('Tuesday')
        WEDNESDAY = 2, _('Wednesday')
        THURSDAY = 3, _('Thursday')
        FRIDAY = 4, _('Friday')
        SATURDAY = 5, _('Saturday')
        SUNDAY = 6, _('Sunday')

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_start_time = models.TimeField(null=True, blank=True)
    break_end_time = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    max_appointments = models.PositiveIntegerField(default=0, help_text=_('0 means no limit'))
    appointment_duration = models.PositiveIntegerField(default=30, help_text=_('Duration in minutes'))
    buffer_time = models.PositiveIntegerField(default=0, help_text=_('Buffer time between appointments in minutes'))

    class Meta:
        unique_together = ['doctor', 'clinic', 'day_of_week']
        verbose_name = _('Schedule')
        verbose_name_plural = _('Schedules')
        ordering = ['doctor', 'clinic', 'day_of_week']

    def __str__(self):
        return f"{self.doctor} at {self.clinic} on {self.get_day_of_week_display()}"


class ScheduleException(TimeStampedModel):
    """
    Model representing exceptions to a doctor's regular schedule.
    """

    class ExceptionType(models.TextChoices):
        VACATION = 'vacation', _('Vacation')
        SICK_LEAVE = 'sick_leave', _('Sick Leave')
        PERSONAL_LEAVE = 'personal_leave', _('Personal Leave')
        CONFERENCE = 'conference', _('Conference')
        HOLIDAY = 'holiday', _('Holiday')
        OTHER = 'other', _('Other')

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedule_exceptions')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='schedule_exceptions')
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True, help_text=_('If not specified, whole day is excepted'))
    end_time = models.TimeField(null=True, blank=True, help_text=_('If not specified, end of day is assumed'))
    exception_type = models.CharField(max_length=20, choices=ExceptionType.choices)
    reason = models.TextField(blank=True, null=True)
    is_recurring = models.BooleanField(default=False)
    recurring_until = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = _('Schedule Exception')
        verbose_name_plural = _('Schedule Exceptions')
        ordering = ['start_date', 'start_time']

    def __str__(self):
        return f"{self.doctor} exception from {self.start_date} to {self.end_date}"


class TimeSlot(TimeStampedModel):
    """
    Model representing available time slots for appointments.
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='time_slots')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='time_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    is_booked = models.BooleanField(default=False)
    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_slot'
    )

    class Meta:
        unique_together = ['doctor', 'clinic', 'date', 'start_time']
        verbose_name = _('Time Slot')
        verbose_name_plural = _('Time Slots')
        ordering = ['date', 'start_time']

    def __str__(self):
        status = "Available" if self.is_available and not self.is_booked else "Not Available"
        return f"{self.doctor} at {self.clinic} on {self.date} at {self.start_time.strftime('%H:%M')} ({status})"


class AvailabilityPreference(TimeStampedModel):
    """
    Model representing a doctor's preferences for availability.
    """
    doctor = models.OneToOneField(Doctor, on_delete=models.CASCADE, related_name='availability_preference')
    preferred_working_days = models.JSONField(default=list, blank=True, help_text=_('List of preferred days (0-6)'))
    preferred_start_time = models.TimeField(null=True, blank=True)
    preferred_end_time = models.TimeField(null=True, blank=True)
    preferred_appointment_duration = models.PositiveIntegerField(default=30, help_text=_('Duration in minutes'))
    preferred_buffer_time = models.PositiveIntegerField(default=0,
                                                        help_text=_('Buffer time between appointments in minutes'))
    max_appointments_per_day = models.PositiveIntegerField(default=0, help_text=_('0 means no limit'))
    max_consecutive_days = models.PositiveIntegerField(default=0, help_text=_('0 means no limit'))
    preferred_break_start_time = models.TimeField(null=True, blank=True)
    preferred_break_end_time = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _('Availability Preference')
        verbose_name_plural = _('Availability Preferences')

    def __str__(self):
        return f"Availability preferences for {self.doctor}"