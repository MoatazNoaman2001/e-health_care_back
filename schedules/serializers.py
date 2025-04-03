from rest_framework import serializers
from doctors.serializers import DoctorSerializer
from clinics.serializers import ClinicSerializer
from .models import Schedule, ScheduleException, TimeSlot, AvailabilityPreference


class ScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Schedule model.
    """
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = Schedule
        fields = [
            'id', 'doctor', 'clinic', 'day_of_week', 'day_name', 'start_time',
            'end_time', 'break_start_time', 'break_end_time', 'is_active',
            'max_appointments', 'appointment_duration', 'buffer_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ScheduleDetailSerializer(ScheduleSerializer):
    """
    Detailed serializer for Schedule including related data.
    """
    doctor = DoctorSerializer(read_only=True)
    clinic = ClinicSerializer(read_only=True)

    class Meta(ScheduleSerializer.Meta):
        pass


class ScheduleExceptionSerializer(serializers.ModelSerializer):
    """
    Serializer for the ScheduleException model.
    """
    exception_type_display = serializers.CharField(source='get_exception_type_display', read_only=True)

    class Meta:
        model = ScheduleException
        fields = [
            'id', 'doctor', 'clinic', 'start_date', 'end_date', 'start_time',
            'end_time', 'exception_type', 'exception_type_display', 'reason',
            'is_recurring', 'recurring_until', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ScheduleExceptionDetailSerializer(ScheduleExceptionSerializer):
    """
    Detailed serializer for ScheduleException including related data.
    """
    doctor = DoctorSerializer(read_only=True)
    clinic = ClinicSerializer(read_only=True)

    class Meta(ScheduleExceptionSerializer.Meta):
        pass


class TimeSlotSerializer(serializers.ModelSerializer):
    """
    Serializer for the TimeSlot model.
    """

    class Meta:
        model = TimeSlot
        fields = [
            'id', 'doctor', 'clinic', 'date', 'start_time', 'end_time',
            'is_available', 'is_booked', 'appointment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TimeSlotDetailSerializer(TimeSlotSerializer):
    """
    Detailed serializer for TimeSlot including related data.
    """
    doctor = DoctorSerializer(read_only=True)
    clinic = ClinicSerializer(read_only=True)

    class Meta(TimeSlotSerializer.Meta):
        pass


class AvailabilityPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for the AvailabilityPreference model.
    """

    class Meta:
        model = AvailabilityPreference
        fields = [
            'id', 'doctor', 'preferred_working_days', 'preferred_start_time',
            'preferred_end_time', 'preferred_appointment_duration', 'preferred_buffer_time',
            'max_appointments_per_day', 'max_consecutive_days', 'preferred_break_start_time',
            'preferred_break_end_time', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AvailabilityPreferenceDetailSerializer(AvailabilityPreferenceSerializer):
    """
    Detailed serializer for AvailabilityPreference including related data.
    """
    doctor = DoctorSerializer(read_only=True)

    class Meta(AvailabilityPreferenceSerializer.Meta):
        pass


class DoctorAvailabilitySerializer(serializers.Serializer):
    """
    Serializer for doctor availability data.
    """
    doctor_id = serializers.IntegerField()
    clinic_id = serializers.IntegerField()
    date = serializers.DateField()

    def validate(self, data):
        """
        Validate that the doctor and clinic exist.
        """
        from doctors.models import Doctor
        from clinics.models import Clinic

        try:
            doctor = Doctor.objects.get(id=data['doctor_id'])
        except Doctor.DoesNotExist:
            raise serializers.ValidationError({'doctor_id': 'Doctor not found.'})

        try:
            clinic = Clinic.objects.get(id=data['clinic_id'])
        except Clinic.DoesNotExist:
            raise serializers.ValidationError({'clinic_id': 'Clinic not found.'})

        # Check if doctor works at clinic
        from clinics.models import DoctorClinic
        if not DoctorClinic.objects.filter(doctor=doctor, clinic=clinic).exists():
            raise serializers.ValidationError('Doctor does not work at this clinic.')

        return data


class TimeSlotGenerationSerializer(serializers.Serializer):
    """
    Serializer for generating time slots.
    """
    doctor_id = serializers.IntegerField()
    clinic_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, data):
        """
        Validate that the doctor and clinic exist and the date range is valid.
        """
        from doctors.models import Doctor
        from clinics.models import Clinic

        try:
            doctor = Doctor.objects.get(id=data['doctor_id'])
        except Doctor.DoesNotExist:
            raise serializers.ValidationError({'doctor_id': 'Doctor not found.'})

        try:
            clinic = Clinic.objects.get(id=data['clinic_id'])
        except Clinic.DoesNotExist:
            raise serializers.ValidationError({'clinic_id': 'Clinic not found.'})

        # Check if doctor works at clinic
        from clinics.models import DoctorClinic
        if not DoctorClinic.objects.filter(doctor=doctor, clinic=clinic).exists():
            raise serializers.ValidationError('Doctor does not work at this clinic.')

        # Validate date range
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError('Start date must be before end date.')

        # Limit the range to prevent too many slots being generated at once
        from datetime import timedelta
        max_range = timedelta(days=90)  # 3 months
        if data['end_date'] - data['start_date'] > max_range:
            raise serializers.ValidationError(f'Date range cannot exceed {max_range.days} days.')

        return data