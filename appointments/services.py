from datetime import timedelta
from django.utils import timezone
from .models import AppointmentReminder


def create_appointment_reminders(appointment):
    """
    Create reminders for an appointment.

    Args:
        appointment: The appointment instance
    """
    # Calculate reminder times
    appointment_datetime = timezone.make_aware(
        timezone.datetime.combine(appointment.scheduled_date, appointment.scheduled_time)
    )

    # Create reminders: 1 day before, 3 hours before, and 30 minutes before
    reminder_times = [
        appointment_datetime - timedelta(days=1),
        appointment_datetime - timedelta(hours=3),
        appointment_datetime - timedelta(minutes=30)
    ]

    # Create email reminders
    for scheduled_time in reminder_times:
        # Skip if reminder time is in the past
        if scheduled_time <= timezone.now():
            continue

        AppointmentReminder.objects.create(
            appointment=appointment,
            reminder_type='email',
            scheduled_time=scheduled_time,
            status='pending'
        )

    # Create SMS reminders (only 1 day before and 1 hour before)
    sms_reminder_times = [
        appointment_datetime - timedelta(days=1),
        appointment_datetime - timedelta(hours=1)
    ]

    for scheduled_time in sms_reminder_times:
        # Skip if reminder time is in the past
        if scheduled_time <= timezone.now():
            continue

        AppointmentReminder.objects.create(
            appointment=appointment,
            reminder_type='sms',
            scheduled_time=scheduled_time,
            status='pending'
        )


def send_appointment_confirmation(appointment):
    """
    Send confirmation email/SMS for a new appointment.

    Args:
        appointment: The appointment instance
    """
    # In a real application, this would send actual emails/SMS
    # For now, we'll just mark that a confirmation was sent
    appointment.reminder_sent = True
    appointment.save(update_fields=['reminder_sent'])

    # Log that confirmation was sent
    print(f"Appointment confirmation sent for appointment #{appointment.id}")


def check_doctor_availability(doctor, clinic, scheduled_date, scheduled_time, duration=30, exclude_appointment_id=None):
    """
    Check if a doctor is available for an appointment at the specified time.

    Args:
        doctor: The doctor instance
        clinic: The clinic instance
        scheduled_date: The date for the appointment
        scheduled_time: The time for the appointment
        duration: The duration of the appointment in minutes
        exclude_appointment_id: Appointment ID to exclude from the check (for rescheduling)

    Returns:
        bool: True if doctor is available, False otherwise
    """
    from .models import Appointment
    from django.db.models import Q

    # Check if doctor works at this clinic
    from ..clinics.models import DoctorClinic
    if not DoctorClinic.objects.filter(doctor=doctor, clinic=clinic).exists():
        return False

    # Calculate start and end time of the appointment
    appointment_start = timezone.make_aware(
        timezone.datetime.combine(scheduled_date, scheduled_time)
    )
    appointment_end = appointment_start + timedelta(minutes=duration)

    # Check for overlapping appointments
    overlapping_appointments = Appointment.objects.filter(
        doctor=doctor,
        scheduled_date=scheduled_date,
        status__in=['scheduled', 'confirmed', 'rescheduled']
    )

    if exclude_appointment_id:
        overlapping_appointments = overlapping_appointments.exclude(id=exclude_appointment_id)

    for existing_appointment in overlapping_appointments:
        existing_start = timezone.make_aware(
            timezone.datetime.combine(existing_appointment.scheduled_date, existing_appointment.scheduled_time)
        )
        existing_end = existing_start + timedelta(minutes=existing_appointment.duration)

        # Check for overlap
        if (appointment_start < existing_end and appointment_end > existing_start):
            return False

    return True


def get_doctor_available_slots(doctor, clinic, date, duration=30):
    """
    Get available time slots for a doctor on a specific date.

    Args:
        doctor: The doctor instance
        clinic: The clinic instance
        date: The date to check
        duration: The appointment duration in minutes

    Returns:
        list: List of available time slots (time objects)
    """
    from ..schedules.models import Schedule
    from .models import Appointment
    import datetime

    # Get the day of week (0 for Monday, 6 for Sunday)
    day_of_week = date.weekday()

    # Check if doctor has a schedule for this day at this clinic
    try:
        schedule = Schedule.objects.get(doctor=doctor, clinic=clinic, day_of_week=day_of_week)
    except Schedule.DoesNotExist:
        # Doctor doesn't work on this day at this clinic
        return []

    # Get doctor's working hours
    start_time = schedule.start_time
    end_time = schedule.end_time

    if start_time is None or end_time is None:
        return []

    # Generate all possible slots
    slots = []
    current_time = start_time

    # Create slots every 'duration' minutes
    while current_time <= (datetime.datetime.combine(date, end_time) - timedelta(minutes=duration)).time():
        slots.append(current_time)
        current_time_dt = datetime.datetime.combine(date, current_time) + timedelta(minutes=duration)
        current_time = current_time_dt.time()

    # Get all appointments for this doctor on this date
    appointments = Appointment.objects.filter(
        doctor=doctor,
        clinic=clinic,
        scheduled_date=date,
        status__in=['scheduled', 'confirmed', 'rescheduled']
    )

    # Remove slots that overlap with existing appointments
    available_slots = slots.copy()
    for appointment in appointments:
        appointment_start = appointment.scheduled_time
        appointment_end = (
                    datetime.datetime.combine(date, appointment_start) + timedelta(minutes=appointment.duration)).time()

        # Remove slots that would overlap with this appointment
        slots_to_remove = []
        for slot in available_slots:
            slot_end = (datetime.datetime.combine(date, slot) + timedelta(minutes=duration)).time()

            # Check for overlap
            if (slot < appointment_end and slot_end > appointment_start):
                slots_to_remove.append(slot)

        for slot in slots_to_remove:
            if slot in available_slots:
                available_slots.remove(slot)

    return available_slots


def get_appointment_statistics(start_date=None, end_date=None, doctor=None, clinic=None):
    """
    Get statistics about appointments.

    Args:
        start_date: Start date for the statistics
        end_date: End date for the statistics
        doctor: Filter by doctor
        clinic: Filter by clinic

    Returns:
        dict: Dictionary with statistics
    """
    from .models import Appointment
    from django.db.models import Count

    # Initialize filters
    filters = {}

    if start_date:
        filters['scheduled_date__gte'] = start_date

    if end_date:
        filters['scheduled_date__lte'] = end_date

    if doctor:
        filters['doctor'] = doctor

    if clinic:
        filters['clinic'] = clinic

    # Base queryset
    queryset = Appointment.objects.filter(**filters)

    # Calculate statistics
    total_appointments = queryset.count()

    status_counts = queryset.values('status').annotate(count=Count('id'))
    status_stats = {item['status']: item['count'] for item in status_counts}

    type_counts = queryset.values('appointment_type').annotate(count=Count('id'))
    type_stats = {item['appointment_type']: item['count'] for item in type_counts}

    # Calculate no-show rate
    no_show_count = status_stats.get('no_show', 0)
    no_show_rate = (no_show_count / total_appointments) * 100 if total_appointments > 0 else 0

    # Calculate cancellation rate
    cancellation_count = status_stats.get('cancelled', 0)
    cancellation_rate = (cancellation_count / total_appointments) * 100 if total_appointments > 0 else 0

    return {
        'total_appointments': total_appointments,
        'status_stats': status_stats,
        'type_stats': type_stats,
        'no_show_rate': no_show_rate,
        'cancellation_rate': cancellation_rate
    }