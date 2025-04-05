from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from healthcare_project.accounts.permissions import IsDoctorUser, IsAdminUser
from healthcare_project.common.permissions import IsOwner
from .models import (
    Doctor, Specialization, DoctorEducation, DoctorWorkExperience,
    DoctorCertification, InsuranceProvider, DoctorInsurance
)
from .serializers import (
    DoctorSerializer, DoctorDetailSerializer, DoctorRegistrationSerializer,
    SpecializationSerializer, DoctorEducationSerializer,
    DoctorWorkExperienceSerializer, DoctorCertificationSerializer,
    InsuranceProviderSerializer, DoctorInsuranceSerializer
)
from .filters import DoctorFilter
import serializers


class SpecializationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Specialization instances.
    """
    queryset = Specialization.objects.all()
    serializer_class = SpecializationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsAdminUser()]


class InsuranceProviderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing InsuranceProvider instances.
    """
    queryset = InsuranceProvider.objects.all()
    serializer_class = InsuranceProviderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsAdminUser()]


class DoctorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Doctor instances.
    """
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DoctorFilter
    search_fields = ['first_name', 'last_name', 'specializations__name']
    ordering_fields = ['created_at', 'last_name', 'first_name', 'avg_rating', 'years_of_experience']
    ordering = ['-created_at']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create' or self.action == 'register':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwner | IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'retrieve' or self.action == 'me':
            return DoctorDetailSerializer
        elif self.action == 'register':
            return DoctorRegistrationSerializer
        return self.serializer_class

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """
        Register a new doctor with a user account.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doctor = serializer.save()

        return Response(
            DoctorSerializer(doctor).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsDoctorUser])
    def me(self, request):
        """
        Return the doctor profile of the authenticated user.
        """
        try:
            doctor = Doctor.objects.get(user=request.user)
            serializer = self.get_serializer(doctor)
            return Response(serializer.data)
        except Doctor.DoesNotExist:
            return Response(
                {'detail': 'Doctor profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_insurance(self, request, pk=None):
        """
        Add an insurance provider to a doctor's accepted insurances.
        """
        doctor = self.get_object()

        # Check if user has permission
        if not (request.user.is_staff or (hasattr(request.user, 'doctor') and request.user.doctor == doctor)):
            return Response(
                {'detail': 'You do not have permission to perform this action.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = DoctorInsuranceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        insurance = serializer.validated_data['insurance']

        # Check if already exists
        if DoctorInsurance.objects.filter(doctor=doctor, insurance=insurance).exists():
            return Response(
                {'detail': 'This insurance provider is already added.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        doctor_insurance = DoctorInsurance.objects.create(doctor=doctor, insurance=insurance)

        return Response(
            DoctorInsuranceSerializer(doctor_insurance).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def remove_insurance(self, request, pk=None):
        """
        Remove an insurance provider from a doctor's accepted insurances.
        """
        doctor = self.get_object()

        # Check if user has permission
        if not (request.user.is_staff or (hasattr(request.user, 'doctor') and request.user.doctor == doctor)):
            return Response(
                {'detail': 'You do not have permission to perform this action.'},
                status=status.HTTP_403_FORBIDDEN
            )

        insurance_id = request.data.get('insurance_id')
        if not insurance_id:
            return Response(
                {'detail': 'Insurance ID is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            doctor_insurance = DoctorInsurance.objects.get(doctor=doctor, insurance_id=insurance_id)
            doctor_insurance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DoctorInsurance.DoesNotExist:
            return Response(
                {'detail': 'Insurance not found for this doctor.'},
                status=status.HTTP_404_NOT_FOUND
            )


class DoctorEducationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing DoctorEducation instances.
    """
    queryset = DoctorEducation.objects.all()
    serializer_class = DoctorEducationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Restricts the returned educations to those of the requesting user's doctor profile
        or all for admin users.
        """
        queryset = self.queryset
        user = self.request.user

        if hasattr(user, 'doctor'):
            queryset = queryset.filter(doctor=user.doctor)
        elif not user.is_staff:
            queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        """
        Set the doctor when creating a new education record.
        """
        doctor_id = self.request.data.get('doctor_id')

        if doctor_id:
            try:
                doctor = Doctor.objects.get(id=doctor_id)
                # Check if user has permission
                if self.request.user.is_staff or (
                        hasattr(self.request.user, 'doctor') and self.request.user.doctor == doctor):
                    serializer.save(doctor=doctor)
                else:
                    raise PermissionError("You don't have permission to add education to this doctor.")
            except Doctor.DoesNotExist:
                raise serializers.ValidationError({"doctor_id": "Doctor not found."})
        elif hasattr(self.request.user, 'doctor'):
            serializer.save(doctor=self.request.user.doctor)
        else:
            raise serializers.ValidationError({"doctor_id": "Doctor ID is required."})


class DoctorWorkExperienceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing DoctorWorkExperience instances.
    """
    queryset = DoctorWorkExperience.objects.all()
    serializer_class = DoctorWorkExperienceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Restricts the returned work experiences to those of the requesting user's doctor profile
        or all for admin users.
        """
        queryset = self.queryset
        user = self.request.user

        if hasattr(user, 'doctor'):
            queryset = queryset.filter(doctor=user.doctor)
        elif not user.is_staff:
            queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        """
        Set the doctor when creating a new work experience record.
        """
        doctor_id = self.request.data.get('doctor_id')

        if doctor_id:
            try:
                doctor = Doctor.objects.get(id=doctor_id)
                # Check if user has permission
                if self.request.user.is_staff or (
                        hasattr(self.request.user, 'doctor') and self.request.user.doctor == doctor):
                    serializer.save(doctor=doctor)
                else:
                    raise PermissionError("You don't have permission to add work experience to this doctor.")
            except Doctor.DoesNotExist:
                raise serializers.ValidationError({"doctor_id": "Doctor not found."})
        elif hasattr(self.request.user, 'doctor'):
            serializer.save(doctor=self.request.user.doctor)
        else:
            raise serializers.ValidationError({"doctor_id": "Doctor ID is required."})


class DoctorCertificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing DoctorCertification instances.
    """
    queryset = DoctorCertification.objects.all()
    serializer_class = DoctorCertificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Restricts the returned certifications to those of the requesting user's doctor profile
        or all for admin users.
        """
        queryset = self.queryset
        user = self.request.user

        if hasattr(user, 'doctor'):
            queryset = queryset.filter(doctor=user.doctor)
        elif not user.is_staff:
            queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        """
        Set the doctor when creating a new certification record.
        """
        doctor_id = self.request.data.get('doctor_id')

        if doctor_id:
            try:
                doctor = Doctor.objects.get(id=doctor_id)
                # Check if user has permission
                if self.request.user.is_staff or (
                        hasattr(self.request.user, 'doctor') and self.request.user.doctor == doctor):
                    serializer.save(doctor=doctor)
                else:
                    raise PermissionError("You don't have permission to add certification to this doctor.")
            except Doctor.DoesNotExist:
                raise serializers.ValidationError({"doctor_id": "Doctor not found."})
        elif hasattr(self.request.user, 'doctor'):
            serializer.save(doctor=self.request.user.doctor)
        else:
            raise serializers.ValidationError({"doctor_id": "Doctor ID is required."})