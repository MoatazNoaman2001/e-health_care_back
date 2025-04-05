from celery import shared_task
from django.utils import timezone
from .models import Appointment, AppointmentReminder


@shared_task
def send_appointment_reminders():
    """
    Celery task to send pending appointment reminders.
    """
    now = timezone.now()

    # Get all pending reminders that are due to be sent
    pending_reminders = AppointmentReminder.objects.filter(
        status='pending',
        scheduled_time__lte=now
    )

    for reminder in pending_reminders:
        try:
            # Only send reminders for appointments that are still active
            if reminder.appointment.status in ['scheduled', 'confirmed', 'rescheduled']:
                send_reminder(reminder)

                # Update reminder status
                reminder.sent_at = timezone.now()
                reminder.status = 'sent'
                reminder.save()
            else:
                # Appointment is no longer active, cancel the reminder
                reminder.status = 'cancelled'
                reminder.save()
        except Exception as e:
            # Log the error and mark the reminder as failed
            reminder.status = 'failed'
            reminder.error_message = str(e)
            reminder.save()


def send_reminder(reminder):
    """
    Send an appointment reminder based on its type.

    Args:
        reminder: The AppointmentReminder instance
    """
    appointment = reminder.appointment

    if reminder.reminder_type == 'email':
        send_email_reminder(appointment)
    elif reminder.reminder_type == 'sms':
        send_sms_reminder(appointment)
    elif reminder.reminder_type == 'push':
        send_push_reminder(appointment)


def send_email_reminder(appointment):
    """
    Send an email reminder for an appointment.

    Args:
        appointment: The Appointment instance
    """
    # In a real application, this would send an actual email
    # For now, we'll just print a message
    print(f"Email reminder sent for appointment #{appointment.id}")

    # Example of how this might be implemented in a real application:
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string

    # Get email recipient
    patient_email = appointment.patient.user.email

    # Prepare the email content
    subject = f"Reminder: Your appointment on {appointment.scheduled_date}"
    context = {
        'appointment': appointment,
        'patient_name': appointment.patient.first_name,
        'doctor_name': appointment.doctor.full_name,
        'clinic_name': appointment.clinic.name,
        'appointment_date': appointment.scheduled_date,
        'appointment_time': appointment.formatted_time,
    }
    html_message = render_to_string('emails/appointment_reminder.html', context)
    plain_message = render_to_string('emails/appointment_reminder.txt', context)

    # Send the email
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[patient_email],
        html_message=html_message,
    )
    """


def send_sms_reminder(appointment):
    """
    Send an SMS reminder for an appointment.

    Args:
        appointment: The Appointment instance
    """
    # In a real application, this would send an actual SMS
    # using a service like Twilio
    # For now, we'll just print a message
    print(f"SMS reminder sent for appointment #{appointment.id}")

    # Example of how this might be implemented using Twilio:
    """
    from twilio.rest import Client

    # Get SMS recipient
    patient_phone = appointment.patient.phone_number

    # Prepare the SMS content
    message = (
        f"Reminder: You have an appointment with Dr. {appointment.doctor.last_name} "
        f"at {appointment.clinic.name} on {appointment.scheduled_date} "
        f"at {appointment.formatted_time}."
    )

    # Send the SMS
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=patient_phone
    )
    """


def send_push_reminder(appointment):
    """
    Send a push notification reminder for an appointment.

    Args:
        appointment: The Appointment instance
    """
    # In a real application, this would send an actual push notification
    # using a service like Firebase Cloud Messaging
    # For now, we'll just print a message
    print(f"Push notification reminder sent for appointment #{appointment.id}")

    # Example of how this might be implemented using Firebase:
    """
    import firebase_admin
    from firebase_admin import messaging

    # Get the user's device token(s) from the database
    # This would require a model to store user device tokens
    device_tokens = UserDevice.objects.filter(user=appointment.patient.user).values_list('device_token', flat=True)

    if not device_tokens:
        return

    # Prepare the notification
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=f"Upcoming Appointment Reminder",
            body=f"You have an appointment with Dr. {appointment.doctor.last_name} at {appointment.formatted_time}."
        ),
        data={
            'appointment_id': str(appointment.id),
            'type': 'appointment_reminder'
        },
        tokens=list(device_tokens)
    )

    # Send the notification
    response = messaging.send_multicast(message)
    print(f"{response.success_count} messages were sent successfully")
    """


@shared_task
def update_appointment_statuses():
    """
    Celery task to update appointment statuses based on time.
    """
    now = timezone.now()
    today = now.date()

    # Mark past appointments as "no_show" if they were scheduled and not completed
    past_appointments = Appointment.objects.filter(
        scheduled_date__lt=today,
        status__in=['scheduled', 'confirmed', 'rescheduled']
    )

    past_appointments.update(
        status=Appointment.AppointmentStatus.NO_SHOW
    )

    # Check today's appointments that have passed
    today_appointments = Appointment.objects.filter(
        scheduled_date=today,
        status__in=['scheduled', 'confirmed', 'rescheduled']
    )

    for appointment in today_appointments:
        appointment_time = timezone.make_aware(
            timezone.datetime.combine(appointment.scheduled_date, appointment.scheduled_time)
        )
        appointment_end_time = appointment_time + timezone.timedelta(minutes=appointment.duration)

        # If appointment has ended and status hasn't been updated, mark as no-show
        if appointment_end_time < now:
            appointment.status = Appointment.AppointmentStatus.NO_SHOW
            appointment.save()


@shared_task
def send_followup_reminders():
    """
    Celery task to send reminders for follow-up appointments.
    """
    now = timezone.now()

    # Get completed appointments that have followup_date set to today
    # and haven't had a followup appointment created yet
    followup_appointments = Appointment.objects.filter(
        status='completed',
        followup_date=now.date(),
        # This would require a field to track whether a followup has been scheduled
        followup_scheduled=False
    )

    for appointment in followup_appointments:
        send_followup_reminder(appointment)


def send_followup_reminder(appointment):
    """
    Send a reminder to schedule a follow-up appointment.

    Args:
        appointment: The Appointment instance
    """
    # In a real application, this would send an actual email or SMS
    # For now, we'll just print a message
    print(f"Follow-up reminder sent for appointment #{appointment.id}")

    # Example of how this might be implemented in a real application:
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string

    # Get email recipient
    patient_email = appointment.patient.user.email

    # Prepare the email content
    subject = f"Time to schedule your follow-up appointment"
    context = {
        'appointment': appointment,
        'patient_name': appointment.patient.first_name,
        'doctor_name': appointment.doctor.full_name,
        'clinic_name': appointment.clinic.name,
        'followup_date': appointment.followup_date,
    }
    html_message = render_to_string('emails/followup_reminder.html', context)
    plain_message = render_to_string('emails/followup_reminder.txt', context)

    # Send the email
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[patient_email],
        html_message=html_message,
    )
    """