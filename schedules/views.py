from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from healthcare_project.doctors.models import Doctor
from healthcare_project.clinics.models import Clinic
from healthcare_project.accounts.permissions import IsDoctorUser, IsAdminUser
from healthcare_project.common.permissions import IsOwner
from .models import Schedule, ScheduleException, TimeSlot, AvailabilityPreference
from .serializers import (
    ScheduleSerializer, ScheduleDetailSerializer,
    ScheduleExceptionSerializer, ScheduleExceptionDetailSerializer,
    TimeSlotSerializer, TimeSlotDetailSerializer,
    AvailabilityPreferenceSerializer, AvailabilityPreferenceDetailSerializer,
    DoctorAvailabilitySerializer, TimeSlotGenerationSerializer
)
from .services import (
    generate_time_slots, get_available_slots,
    update_time_slots_availability, check_doctor_availability
)
from .filters import ScheduleFilter, ScheduleExceptionFilter, TimeSlotFilter


class ScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Schedule instances.
    """
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ScheduleFilter
    ordering_fields = ['day_of_week', 'start_time', 'doctor__last_name', 'clinic__name']
    ordering = ['day_of_week', 'start_time']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsDoctorUser | IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'retrieve':
            return ScheduleDetailSerializer
        return self.serializer_class

    def get_queryset(self):
        """
        Filter schedules based on user role.
        """
        queryset = self.queryset
        user = self.request.user

        # Doctor can only see their own schedules
        if hasattr(user, 'doctor'):
            queryset = queryset.filter(doctor=user.doctor)

        return queryset

    def perform_create(self, serializer):
        """
        Set the doctor when creating a schedule if the user is a doctor.
        """
        user = self.request.user

        if hasattr(user, 'doctor') and not self.request.data.get('doctor'):
            serializer.save(doctor=user.doctor)
        else:
            serializer.save()

    @action(detail=False, methods=['get'])
    def by_doctor(self, request):
        """
        Get schedules for a specific doctor.
        """
        doctor_id = request.query_params.get('doctor_id')

        if not doctor_id:
            return Response(
                {'detail': 'Doctor ID is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            doctor = Doctor.objects.get(id=doctor_id)
            schedules = self.get_queryset().filter(doctor=doctor)

            # Apply any additional filters
            schedules = self.filter_queryset(schedules)

            serializer = self.get_serializer(schedules, many=True)
            return Response(serializer.data)
        except Doctor.DoesNotExist:
            return Response(
                {'detail': 'Doctor not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def by_clinic(self, request):
        """
        Get schedules for a specific clinic.
        """
        clinic_id = request.query_params.get('clinic_id')

        if not clinic_id:
            return Response(
                {'detail': 'Clinic ID is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            clinic = Clinic.objects.get(id=clinic_id)
            schedules = self.get_queryset().filter(clinic=clinic)

            # Apply any additional filters
            schedules = self.filter_queryset(schedules)

            serializer = self.get_serializer(schedules, many=True)
            return Response(serializer.data)
        except Clinic.DoesNotExist:
            return Response(
                {'detail': 'Clinic not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class ScheduleExceptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing ScheduleException instances.
    """
    queryset = ScheduleException.objects.all()
    serializer_class = ScheduleExceptionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ScheduleExceptionFilter
    ordering_fields = ['start_date', 'end_date', 'doctor__last_name', 'clinic__name']
    ordering = ['start_date', 'start_time']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsDoctorUser | IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'retrieve':
            return ScheduleExceptionDetailSerializer
        return self.serializer_class

    def get_queryset(self):
        """
        Filter schedule exceptions based on user role.
        """
        queryset = self.queryset
        user = self.request.user

        # Doctor can only see their own schedule exceptions
        if hasattr(user, 'doctor'):
            queryset = queryset.filter(doctor=user.doctor)

        return queryset

    def perform_create(self, serializer):
        """
        Set the doctor when creating a schedule exception if the user is a doctor.
        """
        user = self.request.user

        if hasattr(user, 'doctor') and not self.request.data.get('doctor'):
            serializer.save(doctor=user.doctor)
        else:
            serializer.save()

        # Update time slots availability based on this exception
        exception = serializer.instance
        update_time_slots_availability(exception)

    def perform_update(self, serializer):
        """
        Update time slots availability when a schedule exception is updated.
        """
        serializer.save()
        update_time_slots_availability(serializer.instance)

    def perform_destroy(self, instance):
        """
        Update time slots availability when a schedule exception is deleted.
        """
        # Store the data needed to update slots
        doctor = instance.doctor
        clinic = instance.clinic
        start_date = instance.start_date
        end_date = instance.end_date

        # Delete the instance
        instance.delete()

        # Regenerate time slots for the affected period
        generate_time_slots(doctor, clinic, start_date, end_date)


class TimeSlotViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing TimeSlot instances.
    """
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = TimeSlotFilter
    ordering_fields = ['date', 'start_time', 'doctor__last_name', 'clinic__name']
    ordering = ['date', 'start_time']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsDoctorUser | IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'retrieve':
            return TimeSlotDetailSerializer
        return self.serializer_class

    def get_queryset(self):
        """
        Filter time slots based on user role and query parameters.
        """
        queryset = self.queryset
        user = self.request.user

        # Doctor can only see their own time slots
        if hasattr(user, 'doctor'):
            queryset = queryset.filter(doctor=user.doctor)

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(date__gte=start_date)

        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        # Filter by availability
        is_available = self.request.query_params.get('is_available')
        if is_available is not None:
            is_available = is_available.lower() == 'true'
            queryset = queryset.filter(is_available=is_available)

        # Filter by booking status
        is_booked = self.request.query_params.get('is_booked')
        if is_booked is not None:
            is_booked = is_booked.lower() == 'true'
            queryset = queryset.filter(is_booked=is_booked)

        return queryset

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate time slots for a doctor at a clinic for a date range.
        """
        serializer = TimeSlotGenerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        doctor_id = serializer.validated_data['doctor_id']
        clinic_id = serializer.validated_data['clinic_id']
        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']

        try:
            doctor = Doctor.objects.get(id=doctor_id)
            clinic = Clinic.objects.get(id=clinic_id)

            # Check permissions
            user = request.user
            if hasattr(user, 'doctor') and user.doctor != doctor and not user.is_staff:
                return Response(
                    {'detail': 'You can only generate time slots for yourself.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Generate the time slots
            time_slots = generate_time_slots(doctor, clinic, start_date, end_date)

            return Response({
                'detail': f'Generated {len(time_slots)} time slots.',
                'count': len(time_slots)
            })
        except Doctor.DoesNotExist:
            return Response(
                {'detail': 'Doctor not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Clinic.DoesNotExist:
            return Response(
                {'detail': 'Clinic not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Get available time slots for a doctor at a clinic on a specific date.
        """
        serializer = DoctorAvailabilitySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        doctor_id = serializer.validated_data['doctor_id']
        clinic_id = serializer.validated_data['clinic_id']
        date = serializer.validated_data['date']

        try:
            doctor = Doctor.objects.get(id=doctor_id)
            clinic = Clinic.objects.get(id=clinic_id)

            # Get available slots
            slots = get_available_slots(doctor, clinic, date)

            # Return the slots
            return Response(TimeSlotSerializer(slots, many=True).data)
        except Doctor.DoesNotExist:
            return Response(
                {'detail': 'Doctor not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Clinic.DoesNotExist:
            return Response(
                {'detail': 'Clinic not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class AvailabilityPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing AvailabilityPreference instances.
    """
    queryset = AvailabilityPreference.objects.all()
    serializer_class = AvailabilityPreferenceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['doctor']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsDoctorUser | IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'retrieve':
            return AvailabilityPreferenceDetailSerializer
        return self.serializer_class

    def get_queryset(self):
        """
        Filter availability preferences based on user role.
        """
        queryset = self.queryset
        user = self.request.user

        # Doctor can only see their own availability preferences
        if hasattr(user, 'doctor'):
            queryset = queryset.filter(doctor=user.doctor)

        return queryset

    def perform_create(self, serializer):
        """
        Set the doctor when creating availability preferences if the user is a doctor.
        """
        user = self.request.user

        if hasattr(user, 'doctor') and not self.request.data.get('doctor'):
            serializer.save(doctor=user.doctor)
        else:
            serializer.save()

    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """
        Get the current user's availability preferences.
        """
        user = request.user

        if not hasattr(user, 'doctor'):
            return Response(
                {'detail': 'Only doctors have availability preferences.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            preference = AvailabilityPreference.objects.get(doctor=user.doctor)
            serializer = self.get_serializer(preference)
            return Response(serializer.data)
        except AvailabilityPreference.DoesNotExist:
            return Response(
                {'detail': 'No availability preferences found.'},
                status=status.HTTP_404_NOT_FOUND
            )