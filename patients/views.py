from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from accounts.permissions import IsPatientUser, IsDoctorUser, IsAdminUser
from common.permissions import IsOwner
from .models import Patient, PatientAddress, MedicalHistory, Medication, FamilyMedicalHistory
from .serializers import (
    PatientSerializer, PatientDetailSerializer, PatientRegistrationSerializer,
    PatientAddressSerializer, MedicalHistorySerializer,
    MedicationSerializer, FamilyMedicalHistorySerializer
)
from .filters import PatientFilter


class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Patient instances.
    Provides CRUD operations with proper permission handling.
    """
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PatientFilter
    search_fields = ['first_name', 'last_name', 'user__email']
    ordering_fields = ['created_at', 'last_name', 'first_name', 'date_of_birth']
    ordering = ['-created_at']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        permission_mapping = {
            'create': [permissions.AllowAny],
            'register': [permissions.AllowAny],
            'retrieve': [permissions.IsAuthenticated, IsOwner | IsDoctorUser | IsAdminUser],
            'update': [permissions.IsAuthenticated, IsOwner | IsDoctorUser | IsAdminUser],
            'partial_update': [permissions.IsAuthenticated, IsOwner | IsDoctorUser | IsAdminUser],
            'destroy': [permissions.IsAuthenticated, IsOwner | IsDoctorUser | IsAdminUser],
            'list': [permissions.IsAuthenticated, IsDoctorUser | IsAdminUser],
            'me': [permissions.IsAuthenticated, IsPatientUser],
            # Default for any other actions
            'default': [permissions.IsAuthenticated],
        }

        # Get permission classes for the current action or use default
        permission_classes = permission_mapping.get(self.action, permission_mapping['default'])
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        serializer_mapping = {
            'retrieve': PatientDetailSerializer,
            'me': PatientDetailSerializer,
            'register': PatientRegistrationSerializer,
            # Default serializer for other actions
            'default': PatientSerializer,
        }

        return serializer_mapping.get(self.action, serializer_mapping['default'])

    def get_queryset(self):
        """
        Filter queryset based on user permissions.
        """
        user = self.request.user

        # If not authenticated, return nothing (should be caught by permissions)
        if not user.is_authenticated:
            return Patient.objects.none()

        # For admin users, return all patients
        if user.is_staff:
            return self.queryset

        # For patient users, return only their own data
        if hasattr(user, 'patient'):
            return self.queryset.filter(user=user)

        # For doctor users, return associated patients
        if hasattr(user, 'doctor'):
            # Use select_related or prefetch_related for better performance if needed
            return self.queryset.filter(
                appointments__doctor__user=user
            ).distinct()

        # Default case: no results
        return Patient.objects.none()

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny], authentication_classes=[])
    def register(self, request):
        """
        Register a new patient with a user account.
        """
        try:
            serializer = self.get_serializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            patient = serializer.save()

            return Response(
                PatientSerializer(patient).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            # Log the error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in patient registration: {str(e)}")

            # Return a 500 response
            return Response(
                {"detail": "An error occurred during registration. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsPatientUser])
    def me(self, request):
        """
        Return the patient profile of the authenticated user.
        """
        try:
            patient = Patient.objects.get(user=request.user)
            serializer = self.get_serializer(patient)
            return Response(serializer.data)
        except Patient.DoesNotExist:
            return Response(
                {'detail': 'Patient profile not found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Log the error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in patient me endpoint: {str(e)}")

            # Return a 500 response
            return Response(
                {"detail": "An error occurred while retrieving your profile."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PatientAddressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing PatientAddress instances.
    """
    queryset = PatientAddress.objects.all()
    serializer_class = PatientAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filter addresses to only those belonging to the current user's patient profile
        or patients that the doctor has access to.
        """
        queryset = self.queryset
        user = self.request.user

        # Patient can only see their own addresses
        if hasattr(user, 'patient'):
            queryset = queryset.filter(patient__user=user)

        # Doctor can see addresses of patients they've treated
        elif hasattr(user, 'doctor'):
            queryset = queryset.filter(
                patient__appointments__doctor__user=user
            ).distinct()

        # Admin can see all
        elif user.is_staff:
            pass

        else:
            queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        """
        Set the patient when creating a new address.
        """
        patient_id = self.request.data.get('patient_id')
        if patient_id:
            try:
                patient = Patient.objects.get(id=patient_id)
                # Check if the user is the patient or has permission
                user = self.request.user
                if (hasattr(user, 'patient') and user.patient == patient) or \
                        user.is_staff or (
                        hasattr(user, 'doctor') and patient.appointments.filter(doctor__user=user).exists()):
                    serializer.save(patient=patient)
                else:
                    raise PermissionError("You don't have permission to add an address to this patient.")
            except Patient.DoesNotExist:
                raise serializers.ValidationError({"patient_id": "Patient not found."})
        elif hasattr(self.request.user, 'patient'):
            serializer.save(patient=self.request.user.patient)
        else:
            raise serializers.ValidationError({"patient_id": "Patient ID is required."})


class MedicalHistoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing MedicalHistory instances.
    """
    queryset = MedicalHistory.objects.all()
    serializer_class = MedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['patient', 'condition', 'is_current']
    ordering_fields = ['diagnosis_date', 'created_at']
    ordering = ['-diagnosis_date']

    def get_queryset(self):
        """
        Filter medical history records based on user permissions.
        """
        queryset = self.queryset
        user = self.request.user

        # Patient can only see their own medical history
        if hasattr(user, 'patient'):
            queryset = queryset.filter(patient__user=user)

        # Doctor can see medical history of patients they've treated
        elif hasattr(user, 'doctor'):
            queryset = queryset.filter(
                patient__appointments__doctor__user=user
            ).distinct()

        # Admin can see all
        elif user.is_staff:
            pass

        else:
            queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        """
        Set the patient when creating a new medical history record.
        """
        patient_id = self.request.data.get('patient_id')
        if patient_id:
            try:
                patient = Patient.objects.get(id=patient_id)
                # Check if the user has permission
                user = self.request.user
                if user.is_staff or (
                        hasattr(user, 'doctor') and patient.appointments.filter(doctor__user=user).exists()):
                    serializer.save(patient=patient)
                else:
                    raise PermissionError("You don't have permission to add medical history to this patient.")
            except Patient.DoesNotExist:
                raise serializers.ValidationError({"patient_id": "Patient not found."})
        elif hasattr(self.request.user, 'patient'):
            serializer.save(patient=self.request.user.patient)
        else:
            raise serializers.ValidationError({"patient_id": "Patient ID is required."})


class MedicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Medication instances.
    """
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['patient', 'name', 'is_current']
    search_fields = ['name', 'prescribing_doctor']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']

    def get_queryset(self):
        """
        Filter medications based on user permissions.
        """
        queryset = self.queryset
        user = self.request.user

        # Patient can only see their own medications
        if hasattr(user, 'patient'):
            queryset = queryset.filter(patient__user=user)

        # Doctor can see medications of patients they've treated
        elif hasattr(user, 'doctor'):
            queryset = queryset.filter(
                patient__appointments__doctor__user=user
            ).distinct()

        # Admin can see all
        elif user.is_staff:
            pass

        else:
            queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        """
        Set the patient when creating a new medication record.
        """
        patient_id = self.request.data.get('patient_id')
        if patient_id:
            try:
                patient = Patient.objects.get(id=patient_id)
                # Check if the user has permission
                user = self.request.user
                if user.is_staff or (
                        hasattr(user, 'doctor') and patient.appointments.filter(doctor__user=user).exists()):
                    serializer.save(patient=patient)
                else:
                    raise PermissionError("You don't have permission to add medication to this patient.")
            except Patient.DoesNotExist:
                raise serializers.ValidationError({"patient_id": "Patient not found."})
        elif hasattr(self.request.user, 'patient'):
            serializer.save(patient=self.request.user.patient)
        else:
            raise serializers.ValidationError({"patient_id": "Patient ID is required."})


class FamilyMedicalHistoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing FamilyMedicalHistory instances.
    """
    queryset = FamilyMedicalHistory.objects.all()
    serializer_class = FamilyMedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['patient', 'relationship', 'condition']
    search_fields = ['relationship', 'condition']

    def get_queryset(self):
        """
        Filter family medical history based on user permissions.
        """
        queryset = self.queryset
        user = self.request.user

        # Patient can only see their own family medical history
        if hasattr(user, 'patient'):
            queryset = queryset.filter(patient__user=user)

        # Doctor can see family medical history of patients they've treated
        elif hasattr(user, 'doctor'):
            queryset = queryset.filter(
                patient__appointments__doctor__user=user
            ).distinct()

        # Admin can see all
        elif user.is_staff:
            pass

        else:
            queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        """
        Set the patient when creating a new family medical history record.
        """
        patient_id = self.request.data.get('patient_id')
        if patient_id:
            try:
                patient = Patient.objects.get(id=patient_id)
                # Check if the user has permission
                user = self.request.user
                if (hasattr(user, 'patient') and user.patient == patient) or \
                        user.is_staff or (
                        hasattr(user, 'doctor') and patient.appointments.filter(doctor__user=user).exists()):
                    serializer.save(patient=patient)
                else:
                    raise PermissionError("You don't have permission to add family medical history to this patient.")
            except Patient.DoesNotExist:
                raise serializers.ValidationError({"patient_id": "Patient not found."})
        elif hasattr(self.request.user, 'patient'):
            serializer.save(patient=self.request.user.patient)
        else:
            raise serializers.ValidationError({"patient_id": "Patient ID is required."})