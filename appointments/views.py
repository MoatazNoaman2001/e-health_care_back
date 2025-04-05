from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from healthcare_project.accounts.permissions import IsPatientUser, IsDoctorUser, IsAdminUser
from healthcare_project.common.permissions import IsOwner
from .models import (
    Appointment, AppointmentDocument, MedicalRecord,
    AppointmentReminder, AppointmentFeedback
)
from .serializers import (
    AppointmentSerializer, AppointmentDetailSerializer, AppointmentCreateSerializer,
    AppointmentCancelSerializer, AppointmentRescheduleSerializer,
    AppointmentDocumentSerializer, MedicalRecordSerializer,
    AppointmentReminderSerializer, AppointmentFeedbackSerializer
)
from .filters import AppointmentFilter
from .services import create_appointment_reminders, send_appointment_confirmation
import serializers


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Appointment instances.
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AppointmentFilter
    search_fields = ['patient__first_name', 'patient__last_name', 'doctor__first_name', 'doctor__last_name', 'reason']
    ordering_fields = ['scheduled_date', 'scheduled_time', 'created_at', 'status']
    ordering = ['-scheduled_date', '-scheduled_time']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwner | IsDoctorUser | IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'retrieve':
            return AppointmentDetailSerializer
        elif self.action == 'create':
            return AppointmentCreateSerializer
        elif self.action == 'cancel':
            return AppointmentCancelSerializer
        elif self.action == 'reschedule':
            return AppointmentRescheduleSerializer
        return self.serializer_class

    def get_queryset(self):
        """
        Filter appointments based on user role.
        """
        queryset = self.queryset
        user = self.request.user

        # Patients can only see their own appointments
        if hasattr(user, 'patient'):
            queryset = queryset.filter(patient__user=user)

        # Doctors can only see appointments where they are the doctor
        elif hasattr(user, 'doctor'):
            queryset = queryset.filter(doctor__user=user)

        # Admin can see all appointments
        elif user.is_staff:
            pass

        else:
            queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        """
        Create a new appointment and set up reminders.
        """
        appointment = serializer.save()

        # Create reminders for the appointment
        create_appointment_reminders(appointment)

        # Send confirmation to patient and doctor
        send_appointment_confirmation(appointment)

        return appointment

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        """
        Cancel an appointment.
        """
        appointment = self.get_object()

        # Check if appointment can be cancelled
        if appointment.status in ['completed', 'cancelled', 'no_show']:
            return Response(
                {'detail': 'Cannot cancel an appointment that is already completed, cancelled, or marked as no-show.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Update appointment status
        appointment.status = Appointment.AppointmentStatus.CANCELLED
        appointment.cancellation_reason = serializer.validated_data.get('cancellation_reason')
        appointment.cancelled_by = serializer.validated_data.get('cancelled_by')
        appointment.cancelled_at = timezone.now()
        appointment.save()

        # Cancel any pending reminders
        appointment.reminders.filter(status='pending').update(status='cancelled')

        return Response(
            AppointmentDetailSerializer(appointment).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reschedule(self, request, pk=None):
        """
        Reschedule an appointment.
        """
        appointment = self.get_object()

        # Check if appointment can be rescheduled
        if appointment.status in ['completed', 'no_show']:
            return Response(
                {'detail': 'Cannot reschedule an appointment that is already completed or marked as no-show.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(appointment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Update appointment status and fields
        appointment.status = Appointment.AppointmentStatus.RESCHEDULED
        serializer.save()

        # Cancel existing reminders and create new ones
        appointment.reminders.filter(status='pending').update(status='cancelled')
        create_appointment_reminders(appointment)

        return Response(
            AppointmentDetailSerializer(appointment).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsDoctorUser])
    def complete(self, request, pk=None):
        """
        Mark an appointment as completed.
        """
        appointment = self.get_object()

        # Check if appointment can be marked as completed
        if appointment.status in ['completed', 'cancelled', 'no_show']:
            return Response(
                {
                    'detail': 'Cannot complete an appointment that is already completed, cancelled, or marked as no-show.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = Appointment.AppointmentStatus.COMPLETED
        appointment.save()

        return Response(
            AppointmentDetailSerializer(appointment).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsDoctorUser])
    def no_show(self, request, pk=None):
        """
        Mark an appointment as no-show.
        """
        appointment = self.get_object()

        # Check if appointment can be marked as no-show
        if appointment.status in ['completed', 'cancelled', 'no_show']:
            return Response(
                {
                    'detail': 'Cannot mark an appointment as no-show if it is already completed, cancelled, or marked as no-show.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = Appointment.AppointmentStatus.NO_SHOW
        appointment.save()

        return Response(
            AppointmentDetailSerializer(appointment).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def confirm(self, request, pk=None):
        """
        Confirm an appointment.
        """
        appointment = self.get_object()

        # Check if appointment can be confirmed
        if appointment.status != Appointment.AppointmentStatus.SCHEDULED:
            return Response(
                {'detail': 'Only scheduled appointments can be confirmed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = Appointment.AppointmentStatus.CONFIRMED
        appointment.save()

        return Response(
            AppointmentDetailSerializer(appointment).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Get upcoming appointments for the authenticated user.
        """
        user = request.user
        now = timezone.now()
        today = now.date()

        queryset = self.get_queryset().filter(
            scheduled_date__gte=today,
            status__in=['scheduled', 'confirmed', 'rescheduled']
        )

        # Further filter for appointments today that haven't passed yet
        today_appointments = queryset.filter(scheduled_date=today)
        future_appointments = queryset.filter(scheduled_date__gt=today)

        # For today's appointments, filter out those that have already passed
        valid_today_appointments = []
        for appointment in today_appointments:
            appointment_time = timezone.make_aware(
                timezone.datetime.combine(appointment.scheduled_date, appointment.scheduled_time)
            )
            if appointment_time >= now:
                valid_today_appointments.append(appointment.id)

        queryset = queryset.filter(
            id__in=valid_today_appointments
        ).union(future_appointments)

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def past(self, request):
        """
        Get past appointments for the authenticated user.
        """
        user = request.user
        now = timezone.now()
        today = now.date()

        queryset = self.get_queryset().filter(
            scheduled_date__lt=today
        )

        # Include today's appointments that have already passed
        today_appointments = self.get_queryset().filter(scheduled_date=today)

        past_today_appointments = []
        for appointment in today_appointments:
            appointment_time = timezone.make_aware(
                timezone.datetime.combine(appointment.scheduled_date, appointment.scheduled_time)
            )
            if appointment_time < now:
                past_today_appointments.append(appointment.id)

        queryset = queryset.union(
            self.get_queryset().filter(id__in=past_today_appointments)
        )

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """
        Get today's appointments for the authenticated user.
        """
        user = request.user
        today = timezone.now().date()

        queryset = self.get_queryset().filter(
            scheduled_date=today,
            status__in=['scheduled', 'confirmed', 'rescheduled']
        )

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AppointmentDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing AppointmentDocument instances.
    """
    queryset = AppointmentDocument.objects.all()
    serializer_class = AppointmentDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['appointment', 'document_type']

    def get_queryset(self):
        """
        Filter documents based on user role.
        """
        queryset = self.queryset
        user = self.request.user

        # Patients can only see documents for their own appointments
        if hasattr(user, 'patient'):
            queryset = queryset.filter(appointment__patient__user=user)

        # Doctors can only see documents for appointments where they are the doctor
        elif hasattr(user, 'doctor'):
            queryset = queryset.filter(appointment__doctor__user=user)

        # Admin can see all documents
        elif user.is_staff:
            pass

        else:
            queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        """
        Set the uploader when creating a document.
        """
        appointment_id = self.request.data.get('appointment_id')

        if not appointment_id:
            raise serializers.ValidationError({'appointment_id': 'Appointment ID is required.'})

        try:
            appointment = Appointment.objects.get(id=appointment_id)

            # Check if user has permission to add documents
            user = self.request.user
            if (hasattr(user, 'patient') and appointment.patient.user == user) or \
                    (hasattr(user, 'doctor') and appointment.doctor.user == user) or \
                    user.is_staff:
                serializer.save(appointment=appointment, uploaded_by=user)
            else:
                raise PermissionError("You don't have permission to add documents to this appointment.")
        except Appointment.DoesNotExist:
            raise serializers.ValidationError({'appointment_id': 'Appointment not found.'})


class MedicalRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing MedicalRecord instances.
    """
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['appointment']

    def get_queryset(self):
        """
        Filter medical records based on user role.
        """
        queryset = self.queryset
        user = self.request.user

        # Patients can only see medical records for their own appointments
        if hasattr(user, 'patient'):
            queryset = queryset.filter(appointment__patient__user=user)

        # Doctors can only see medical records for appointments where they are the doctor
        elif hasattr(user, 'doctor'):
            queryset = queryset.filter(appointment__doctor__user=user)

        # Admin can see all medical records
        elif user.is_staff:
            pass

        else:
            queryset = queryset.none()

        return queryset

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsDoctorUser | IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Create a new medical record for an appointment.
        """
        appointment_id = self.request.data.get('appointment_id')

        if not appointment_id:
            raise serializers.ValidationError({'appointment_id': 'Appointment ID is required.'})

        try:
            appointment = Appointment.objects.get(id=appointment_id)

            # Check if user has permission to add medical records
            user = self.request.user
            if (hasattr(user, 'doctor') and appointment.doctor.user == user) or user.is_staff:
                serializer.save(appointment=appointment)
            else:
                raise PermissionError("Only the appointment's doctor or admin can add medical records.")
        except Appointment.DoesNotExist:
            raise serializers.ValidationError({'appointment_id': 'Appointment not found.'})


class AppointmentFeedbackViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing AppointmentFeedback instances.
    """
    queryset = AppointmentFeedback.objects.all()
    serializer_class = AppointmentFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['appointment']

    def get_queryset(self):
        """
        Filter feedback based on user role.
        """
        queryset = self.queryset
        user = self.request.user

        # Patients can only see feedback for their own appointments
        if hasattr(user, 'patient'):
            queryset = queryset.filter(appointment__patient__user=user)

        # Doctors can only see feedback for appointments where they are the doctor
        elif hasattr(user, 'doctor'):
            queryset = queryset.filter(appointment__doctor__user=user)

        # Admin can see all feedback
        elif user.is_staff:
            pass

        else:
            queryset = queryset.none()

        return queryset

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsPatientUser | IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Create a new feedback for an appointment.
        """
        appointment_id = self.request.data.get('appointment_id')

        if not appointment_id:
            raise serializers.ValidationError({'appointment_id': 'Appointment ID is required.'})

        try:
            appointment = Appointment.objects.get(id=appointment_id)

            # Check if user has permission to add feedback
            user = self.request.user
            if (hasattr(user, 'patient') and appointment.patient.user == user) or user.is_staff:
                # Check if feedback already exists
                if AppointmentFeedback.objects.filter(appointment=appointment).exists():
                    raise serializers.ValidationError(
                        {'appointment_id': 'Feedback already exists for this appointment.'})

                serializer.save(appointment=appointment)
            else:
                raise PermissionError("Only the appointment's patient or admin can add feedback.")
        except Appointment.DoesNotExist:
            raise serializers.ValidationError({'appointment_id': 'Appointment not found.'})


class AppointmentReminderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing AppointmentReminder instances.
    """
    queryset = AppointmentReminder.objects.all()
    serializer_class = AppointmentReminderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['appointment', 'reminder_type', 'status']

    def get_queryset(self):
        """
        Filter reminders based on user role.
        """
        queryset = self.queryset
        user = self.request.user

        # Patients can only see reminders for their own appointments
        if hasattr(user, 'patient'):
            queryset = queryset.filter(appointment__patient__user=user)

        # Doctors can only see reminders for appointments where they are the doctor
        elif hasattr(user, 'doctor'):
            queryset = queryset.filter(appointment__doctor__user=user)

        # Admin can see all reminders
        elif user.is_staff:
            pass

        else:
            queryset = queryset.none()

        return queryset