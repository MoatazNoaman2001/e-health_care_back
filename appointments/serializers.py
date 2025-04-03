from rest_framework import serializers
from ..patients.serializers import PatientSerializer
from ..doctors.serializers import DoctorSerializer
from ..clinics.serializers import ClinicSerializer
from ..accounts.serializers import UserSerializer
from .models import (
    Appointment, AppointmentDocument, MedicalRecord,
    AppointmentReminder, AppointmentFeedback
)


class AppointmentDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for AppointmentDocument model.
    """
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = AppointmentDocument
        fields = ['id', 'title', 'file', 'document_type', 'notes',
                  'uploaded_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class MedicalRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for MedicalRecord model.
    """

    class Meta:
        model = MedicalRecord
        fields = ['id', 'vital_signs', 'symptoms', 'diagnosis', 'treatment_plan',
                  'prescription', 'lab_orders', 'notes', 'followup_instructions',
                  'doctor_signature', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AppointmentReminderSerializer(serializers.ModelSerializer):
    """
    Serializer for AppointmentReminder model.
    """

    class Meta:
        model = AppointmentReminder
        fields = ['id', 'reminder_type', 'scheduled_time', 'sent_at',
                  'status', 'error_message', 'created_at', 'updated_at']
        read_only_fields = ['id', 'sent_at', 'status', 'error_message', 'created_at', 'updated_at']


class AppointmentFeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer for AppointmentFeedback model.
    """

    class Meta:
        model = AppointmentFeedback
        fields = ['id', 'rating', 'comments', 'doctor_punctuality',
                  'facility_cleanliness', 'staff_friendliness',
                  'wait_time', 'would_recommend', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AppointmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Appointment model.
    """
    is_past = serializers.BooleanField(read_only=True)
    is_today = serializers.BooleanField(read_only=True)
    formatted_time = serializers.CharField(read_only=True)
    end_time = serializers.TimeField(read_only=True, format='%I:%M %p')

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'doctor', 'clinic', 'appointment_type', 'status',
            'scheduled_date', 'scheduled_time', 'duration', 'reason', 'notes',
            'is_first_visit', 'is_follow_up', 'is_emergency', 'chief_complaint',
            'cancellation_reason', 'cancelled_by', 'cancelled_at', 'reminder_sent',
            'followup_date', 'insurance_verified', 'payment_status',
            'is_past', 'is_today', 'formatted_time', 'end_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AppointmentDetailSerializer(AppointmentSerializer):
    """
    Detailed serializer for Appointment including related data.
    """
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    clinic = ClinicSerializer(read_only=True)
    documents = AppointmentDocumentSerializer(many=True, read_only=True)
    medical_record = MedicalRecordSerializer(read_only=True)
    reminders = AppointmentReminderSerializer(many=True, read_only=True)
    feedback = AppointmentFeedbackSerializer(read_only=True)

    class Meta(AppointmentSerializer.Meta):
        fields = AppointmentSerializer.Meta.fields + [
            'documents', 'medical_record', 'reminders', 'feedback'
        ]


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new appointment.
    """

    class Meta:
        model = Appointment
        fields = [
            'patient', 'doctor', 'clinic', 'appointment_type',
            'scheduled_date', 'scheduled_time', 'duration', 'reason', 'notes',
            'is_first_visit', 'is_follow_up', 'is_emergency', 'chief_complaint'
        ]

    def validate(self, data):
        """
        Validate appointment data.
        """
        # Check if the doctor is available at the specified time
        doctor = data.get('doctor')
        clinic = data.get('clinic')
        scheduled_date = data.get('scheduled_date')
        scheduled_time = data.get('scheduled_time')
        duration = data.get('duration', 30)

        # Check if doctor works at the clinic
        from ..clinics.models import DoctorClinic
        if not DoctorClinic.objects.filter(doctor=doctor, clinic=clinic).exists():
            raise serializers.ValidationError(
                {"doctor": "This doctor does not work at the selected clinic."}
            )

        # Check if the doctor has another appointment at the same time
        from django.utils import timezone
        from datetime import timedelta

        appointment_start = timezone.make_aware(
            timezone.datetime.combine(scheduled_date, scheduled_time)
        )
        appointment_end = appointment_start + timedelta(minutes=duration)

        # Check if there's an overlap with existing appointments
        overlapping_appointments = Appointment.objects.filter(
            doctor=doctor,
            scheduled_date=scheduled_date,
            status__in=['scheduled', 'confirmed']
        ).exclude(id=self.instance.id if self.instance else None)

        for existing_appointment in overlapping_appointments:
            existing_start = timezone.make_aware(
                timezone.datetime.combine(
                    existing_appointment.scheduled_date,
                    existing_appointment.scheduled_time
                )
            )
            existing_end = existing_start + timedelta(minutes=existing_appointment.duration)

            # Check for overlap
            if (appointment_start < existing_end and appointment_end > existing_start):
                raise serializers.ValidationError(
                    {"scheduled_time": "The doctor already has an appointment during this time."}
                )

        return data


class AppointmentCancelSerializer(serializers.ModelSerializer):
    """
    Serializer for cancelling an appointment.
    """

    class Meta:
        model = Appointment
        fields = ['cancellation_reason', 'cancelled_by']

    def validate(self, data):
        """
        Validate cancellation data.
        """
        if not data.get('cancellation_reason'):
            raise serializers.ValidationError(
                {"cancellation_reason": "Cancellation reason is required."}
            )

        if not data.get('cancelled_by'):
            raise serializers.ValidationError(
                {"cancelled_by": "Must specify who cancelled the appointment."}
            )

        return data


class AppointmentRescheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for rescheduling an appointment.
    """

    class Meta:
        model = Appointment
        fields = ['scheduled_date', 'scheduled_time', 'duration', 'notes']

    def validate(self, data):
        """
        Validate rescheduling data.
        """
        # Check if the doctor is available at the new time
        doctor = self.instance.doctor
        clinic = self.instance.clinic
        scheduled_date = data.get('scheduled_date')
        scheduled_time = data.get('scheduled_time')
        duration = data.get('duration', self.instance.duration)

        # Check for overlapping appointments
        from django.utils import timezone
        from datetime import timedelta

        appointment_start = timezone.make_aware(
            timezone.datetime.combine(scheduled_date, scheduled_time)
        )
        appointment_end = appointment_start + timedelta(minutes=duration)

        # Check if there's an overlap with existing appointments
        overlapping_appointments = Appointment.objects.filter(
            doctor=doctor,
            scheduled_date=scheduled_date,
            status__in=['scheduled', 'confirmed']
        ).exclude(id=self.instance.id)

        for existing_appointment in overlapping_appointments:
            existing_start = timezone.make_aware(
                timezone.datetime.combine(
                    existing_appointment.scheduled_date,
                    existing_appointment.scheduled_time
                )
            )
            existing_end = existing_start + timedelta(minutes=existing_appointment.duration)

            # Check for overlap
            if (appointment_start < existing_end and appointment_end > existing_start):
                raise serializers.ValidationError(
                    {"scheduled_time": "The doctor already has an appointment during this time."}
                )

        return data