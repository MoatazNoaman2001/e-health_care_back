from django.utils import timezone
from datetime import datetime, timedelta, time
from .models import Schedule, ScheduleException, TimeSlot


def generate_time_slots(doctor, clinic, start_date, end_date):
    """
    Generate time slots for a doctor at a clinic for a date range.

    Args:
        doctor: Doctor instance
        clinic: Clinic instance
        start_date: Start date
        end_date: End date

    Returns:
        list: List of created TimeSlot instances
    """
    # Get the schedules for this doctor at this clinic
    schedules = Schedule.objects.filter(
        doctor=doctor,
        clinic=clinic,
        is_active=True
    )

    # If no schedules found, return an empty list
    if not schedules.exists():
        return []

    # Get all schedule exceptions for this period
    exceptions = ScheduleException.objects.filter(
        doctor=doctor,
        clinic=clinic,
        start_date__lte=end_date,
        end_date__gte=start_date
    )

    # Store created time slots
    created_slots = []

    # Generate time slots for each day in the range
    current_date = start_date
    while current_date <= end_date:
        # Get the day of week (0 for Monday, 6 for Sunday)
        day_of_week = current_date.weekday()

        # Check if there's a schedule for this day
        try:
            schedule = schedules.get(day_of_week=day_of_week)
        except Schedule.DoesNotExist:
            # No schedule for this day, move to the next day
            current_date += timedelta(days=1)
            continue

        # Check if the entire day is blocked by an exception
        day_blocked = False
        for exception in exceptions:
            if (exception.start_date <= current_date <= exception.end_date and
                    exception.start_time is None and exception.end_time is None):
                day_blocked = True
                break

        if day_blocked:
            # Day is completely blocked, move to the next day
            current_date += timedelta(days=1)
            continue

        # Get the appointment duration and buffer time
        duration = schedule.appointment_duration
        buffer = schedule.buffer_time
        total_slot_time = duration + buffer

        # Calculate the slots
        start_time = schedule.start_time
        end_time = schedule.end_time

        # The break time if applicable
        break_start = schedule.break_start_time
        break_end = schedule.break_end_time

        current_time = start_time
        while True:
            # Convert time to datetime for easier arithmetic
            slot_start_dt = datetime.combine(current_date, current_time)
            slot_end_dt = slot_start_dt + timedelta(minutes=duration)
            slot_end = slot_end_dt.time()

            # Check if the slot end time exceeds the schedule end time
            if slot_end > end_time:
                break

            # Check if slot overlaps with break time
            slot_during_break = False
            if break_start and break_end:
                if not (slot_end <= break_start or current_time >= break_end):
                    slot_during_break = True

            # Check if slot is blocked by any exception
            slot_blocked = False
            for exception in exceptions:
                if exception.start_date <= current_date <= exception.end_date:
                    # If exception has specific times
                    if exception.start_time and exception.end_time:
                        # Check for overlap
                        if not (slot_end <= exception.start_time or current_time >= exception.end_time):
                            slot_blocked = True
                            break

            # Create the slot if it's not during break and not blocked
            if not slot_during_break and not slot_blocked:
                # Check if a slot already exists
                existing_slot = TimeSlot.objects.filter(
                    doctor=doctor,
                    clinic=clinic,
                    date=current_date,
                    start_time=current_time
                ).first()

                if existing_slot:
                    # Update the existing slot if needed
                    if existing_slot.end_time != slot_end or not existing_slot.is_available:
                        existing_slot.end_time = slot_end
                        existing_slot.is_available = True
                        existing_slot.save()
                    created_slots.append(existing_slot)
                else:
                    # Create a new slot
                    slot = TimeSlot.objects.create(
                        doctor=doctor,
                        clinic=clinic,
                        date=current_date,
                        start_time=current_time,
                        end_time=slot_end,
                        is_available=True
                    )
                    created_slots.append(slot)

            # Move to the next slot start time
            slot_start_dt = slot_start_dt + timedelta(minutes=total_slot_time)
            current_time = slot_start_dt.time()

        # Move to the next day
        current_date += timedelta(days=1)

    return created_slots


def get_available_slots(doctor, clinic, date):
    """
    Get available time slots for a doctor at a clinic on a specific date.

    Args:
        doctor: Doctor instance
        clinic: Clinic instance
        date: Date to check

    Returns:
        queryset: QuerySet of available TimeSlot instances
    """
    # Find all time slots for this doctor/clinic/date that are available and not booked
    available_slots = TimeSlot.objects.filter(
        doctor=doctor,
        clinic=clinic,
        date=date,
        is_available=True,
        is_booked=False
    ).order_by('start_time')

    # Filter out slots that are in the past
    now = timezone.now()
    if date == now.date():
        current_time = now.time()
        available_slots = available_slots.filter(start_time__gt=current_time)

    return available_slots


def update_time_slots_availability(exception):
    """
    Update time slots availability based on a schedule exception.

    Args:
        exception: ScheduleException instance
    """
    # Get all time slots that might be affected by this exception
    time_slots = TimeSlot.objects.filter(
        doctor=exception.doctor,
        clinic=exception.clinic,
        date__gte=exception.start_date,
        date__lte=exception.end_date
    )

    for slot in time_slots:
        # Skip if slot is already booked
        if slot.is_booked:
            continue

        # If exception has no specific times, the entire day is blocked
        if exception.start_time is None and exception.end_time is None:
            slot.is_available = False
            slot.save()
            continue

        # If exception has specific times, check for overlap
        if exception.start_time and exception.end_time:
            # Check if slot overlaps with exception time range
            if not (slot.end_time <= exception.start_time or slot.start_time >= exception.end_time):
                slot.is_available = False
                slot.save()


def check_doctor_availability(doctor, clinic, date, start_time, duration=30):
    """
    Check if a doctor is available at a clinic on a specific date and time.

    Args:
        doctor: Doctor instance
        clinic: Clinic instance
        date: Date to check
        start_time: Start time to check
        duration: Duration in minutes

    Returns:
        bool: True if doctor is available, False otherwise
    """
    # Calculate end time
    start_datetime = datetime.combine(date, start_time)
    end_datetime = start_datetime + timedelta(minutes=duration)
    end_time = end_datetime.time()

    # Check if the doctor has a schedule for this day
    day_of_week = date.weekday()
    try:
        schedule = Schedule.objects.get(
            doctor=doctor,
            clinic=clinic,
            day_of_week=day_of_week,
            is_active=True
        )
    except Schedule.DoesNotExist:
        # No schedule for this day
        return False

    # Check if the requested time is within the doctor's schedule
    if start_time < schedule.start_time or end_time > schedule.end_time:
        return False

    # Check if the requested time overlaps with the doctor's break time
    if schedule.break_start_time and schedule.break_end_time:
        if not (end_time <= schedule.break_start_time or start_time >= schedule.break_end_time):
            return False

    # Check if there are any schedule exceptions covering this time
    exceptions = ScheduleException.objects.filter(
        doctor=doctor,
        clinic=clinic,
        start_date__lte=date,
        end_date__gte=date
    )

    for exception in exceptions:
        # If exception has no specific times, the entire day is blocked
        if exception.start_time is None and exception.end_time is None:
            return False

        # If exception has specific times, check for overlap
        if exception.start_time and exception.end_time:
            if not (end_time <= exception.start_time or start_time >= exception.end_time):
                return False

    # Check if the time slot exists and is available
    slot = TimeSlot.objects.filter(
        doctor=doctor,
        clinic=clinic,
        date=date,
        start_time=start_time,
        end_time=end_time,
        is_available=True,
        is_booked=False
    ).first()

    if not slot:
        return False

    return True


def get_doctor_schedule_summary(doctor, start_date=None, end_date=None):
    """
    Get a summary of a doctor's schedule.

    Args:
        doctor: Doctor instance
        start_date: Start date (defaults to today)
        end_date: End date (defaults to 30 days from start_date)

    Returns:
        dict: Dictionary with schedule summary
    """
    # Set default dates if not provided
    if not start_date:
        start_date = timezone.now().date()

    if not end_date:
        end_date = start_date + timedelta(days=30)

    # Get all schedules for this doctor
    schedules = Schedule.objects.filter(
        doctor=doctor,
        is_active=True
    )

    # Get all clinics where the doctor works
    clinics = {schedule.clinic for schedule in schedules}

    # Get all schedule exceptions for this period
    exceptions = ScheduleException.objects.filter(
        doctor=doctor,
        start_date__lte=end_date,
        end_date__gte=start_date
    )

    # Get all time slots for this period
    time_slots = TimeSlot.objects.filter(
        doctor=doctor,
        date__gte=start_date,
        date__lte=end_date
    )

    # Calculate statistics
    total_slots = time_slots.count()
    available_slots = time_slots.filter(is_available=True, is_booked=False).count()
    booked_slots = time_slots.filter(is_booked=True).count()
    unavailable_slots = time_slots.filter(is_available=False).count()

    # Create a summary by day
    daily_summary = {}
    current_date = start_date
    while current_date <= end_date:
        day_slots = time_slots.filter(date=current_date)

        if day_slots.exists():
            day_available = day_slots.filter(is_available=True, is_booked=False).count()
            day_booked = day_slots.filter(is_booked=True).count()
            day_unavailable = day_slots.filter(is_available=False).count()

            daily_summary[current_date.isoformat()] = {
                'total_slots': day_slots.count(),
                'available_slots': day_available,
                'booked_slots': day_booked,
                'unavailable_slots': day_unavailable,
                'clinics': [slot.clinic.name for slot in day_slots.distinct('clinic')]
            }

        current_date += timedelta(days=1)

    return {
        'doctor': f"{doctor.title} {doctor.first_name} {doctor.last_name}",
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'total_slots': total_slots,
        'available_slots': available_slots,
        'booked_slots': booked_slots,
        'unavailable_slots': unavailable_slots,
        'clinics': [clinic.name for clinic in clinics],
        'daily_summary': daily_summary
    }