from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg
from ..accounts.permissions import IsDoctorUser, IsAdminUser
from ..common.permissions import IsOwner
from ..doctors.models import Doctor
from .models import (
    Clinic, ClinicGallery, DoctorClinic, ClinicBusinessHours,
    ClinicSpecialty, ClinicInsurance, ClinicReview
)
from .serializers import (
    ClinicSerializer, ClinicDetailSerializer, ClinicRegistrationSerializer,
    ClinicGallerySerializer, DoctorClinicSerializer, ClinicBusinessHoursSerializer,
    ClinicSpecialtySerializer, ClinicInsuranceSerializer, ClinicReviewSerializer
)
from .filters import ClinicFilter
import serializers


class ClinicViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Clinic instances.
    """
    queryset = Clinic.objects.all()
    serializer_class = ClinicSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ClinicFilter
    search_fields = ['name', 'address', 'city', 'state', 'specialties__name']
    ordering_fields = ['name', 'created_at', 'established_year']
    ordering = ['name']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve', 'search_nearby']:
            permission_classes = [permissions.AllowAny]
        elif self.action in ['create', 'register']:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'retrieve':
            return ClinicDetailSerializer
        elif self.action == 'register':
            return ClinicRegistrationSerializer
        return self.serializer_class

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsAdminUser])
    def register(self, request):
        """
        Register a new clinic with related information.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        clinic = serializer.save()

        return Response(
            ClinicDetailSerializer(clinic).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsAdminUser])
    def add_doctor(self, request, pk=None):
        """
        Add a doctor to a clinic.
        """
        clinic = self.get_object()

        doctor_id = request.data.get('doctor_id')
        is_primary = request.data.get('is_primary', False)

        if not doctor_id:
            return Response(
                {'detail': 'Doctor ID is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            doctor = Doctor.objects.get(id=doctor_id)

            # Check if the relation already exists
            if DoctorClinic.objects.filter(doctor=doctor, clinic=clinic).exists():
                return Response(
                    {'detail': 'Doctor is already associated with this clinic.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create the association
            doctor_clinic = DoctorClinic.objects.create(
                doctor=doctor,
                clinic=clinic,
                is_primary=is_primary
            )

            return Response(
                DoctorClinicSerializer(doctor_clinic).data,
                status=status.HTTP_201_CREATED
            )
        except Doctor.DoesNotExist:
            return Response(
                {'detail': 'Doctor not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated, IsAdminUser])
    def remove_doctor(self, request, pk=None):
        """
        Remove a doctor from a clinic.
        """
        clinic = self.get_object()

        doctor_id = request.data.get('doctor_id')

        if not doctor_id:
            return Response(
                {'detail': 'Doctor ID is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            doctor_clinic = DoctorClinic.objects.get(doctor_id=doctor_id, clinic=clinic)
            doctor_clinic.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        except DoctorClinic.DoesNotExist:
            return Response(
                {'detail': 'Doctor is not associated with this clinic.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def doctors(self, request, pk=None):
        """
        Get all doctors associated with this clinic.
        """
        clinic = self.get_object()
        doctor_clinics = DoctorClinic.objects.filter(clinic=clinic)

        serializer = DoctorClinicSerializer(doctor_clinics, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_review(self, request, pk=None):
        """
        Add a review for the clinic.
        """
        clinic = self.get_object()
        user = request.user

        # Check if user has already reviewed this clinic
        if ClinicReview.objects.filter(clinic=clinic, user=user).exists():
            return Response(
                {'detail': 'You have already reviewed this clinic.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ClinicReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create the review
        review = ClinicReview.objects.create(
            clinic=clinic,
            user=user,
            **serializer.validated_data
        )

        return Response(
            ClinicReviewSerializer(review).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """
        Get all reviews for this clinic.
        """
        clinic = self.get_object()
        reviews = ClinicReview.objects.filter(clinic=clinic)

        serializer = ClinicReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search_nearby(self, request):
        """
        Search for clinics near a specified location.
        """
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')
        radius = request.query_params.get('radius', 10)  # Default 10 km

        if not latitude or not longitude:
            return Response(
                {'detail': 'Latitude and longitude are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            latitude = float(latitude)
            longitude = float(longitude)
            radius = float(radius)
        except ValueError:
            return Response(
                {'detail': 'Invalid coordinates or radius.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use raw SQL for geographical distance calculation
        # This is a basic approximation using the Haversine formula
        from django.db import connection

        query = """
        SELECT id, name, 
               (6371 * acos(cos(radians(%s)) * cos(radians(latitude)) * 
               cos(radians(longitude) - radians(%s)) + sin(radians(%s)) * 
               sin(radians(latitude)))) AS distance 
        FROM clinics_clinic 
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        HAVING distance < %s 
        ORDER BY distance
        """

        with connection.cursor() as cursor:
            cursor.execute(query, [latitude, longitude, latitude, radius])
            result = cursor.fetchall()

        # Get the clinic IDs from the result
        clinic_ids = [row[0] for row in result]

        # Return clinics
        clinics = Clinic.objects.filter(id__in=clinic_ids)
        serializer = self.get_serializer(clinics, many=True)

        return Response(serializer.data)


class ClinicGalleryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing ClinicGallery instances.
    """
    queryset = ClinicGallery.objects.all()
    serializer_class = ClinicGallerySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Optionally restricts the returned gallery images to a given clinic,
        by filtering against a `clinic_id` query parameter in the URL.
        """
        queryset = self.queryset
        clinic_id = self.request.query_params.get('clinic_id', None)

        if clinic_id is not None:
            queryset = queryset.filter(clinic_id=clinic_id)

        return queryset

    def perform_create(self, serializer):
        clinic_id = self.request.data.get('clinic_id')

        if not clinic_id:
            raise serializers.ValidationError({'clinic_id': 'Clinic ID is required.'})

        try:
            clinic = Clinic.objects.get(id=clinic_id)
            serializer.save(clinic=clinic)
        except Clinic.DoesNotExist:
            raise serializers.ValidationError({'clinic_id': 'Clinic not found.'})


class ClinicBusinessHoursViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing ClinicBusinessHours instances.
    """
    queryset = ClinicBusinessHours.objects.all()
    serializer_class = ClinicBusinessHoursSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Optionally restricts the returned business hours to a given clinic,
        by filtering against a `clinic_id` query parameter in the URL.
        """
        queryset = self.queryset
        clinic_id = self.request.query_params.get('clinic_id', None)

        if clinic_id is not None:
            queryset = queryset.filter(clinic_id=clinic_id)

        return queryset

    def perform_create(self, serializer):
        clinic_id = self.request.data.get('clinic_id')

        if not clinic_id:
            raise serializers.ValidationError({'clinic_id': 'Clinic ID is required.'})

        try:
            clinic = Clinic.objects.get(id=clinic_id)
            serializer.save(clinic=clinic)
        except Clinic.DoesNotExist:
            raise serializers.ValidationError({'clinic_id': 'Clinic not found.'})


class ClinicSpecialtyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing ClinicSpecialty instances.
    """
    queryset = ClinicSpecialty.objects.all()
    serializer_class = ClinicSpecialtySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Optionally restricts the returned specialties to a given clinic,
        by filtering against a `clinic_id` query parameter in the URL.
        """
        queryset = self.queryset
        clinic_id = self.request.query_params.get('clinic_id', None)

        if clinic_id is not None:
            queryset = queryset.filter(clinic_id=clinic_id)

        return queryset

    def perform_create(self, serializer):
        clinic_id = self.request.data.get('clinic_id')

        if not clinic_id:
            raise serializers.ValidationError({'clinic_id': 'Clinic ID is required.'})

        try:
            clinic = Clinic.objects.get(id=clinic_id)
            serializer.save(clinic=clinic)
        except Clinic.DoesNotExist:
            raise serializers.ValidationError({'clinic_id': 'Clinic not found.'})


class ClinicReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing ClinicReview instances.
    """
    queryset = ClinicReview.objects.all()
    serializer_class = ClinicReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['clinic', 'rating', 'is_verified']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwner | IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Optionally restricts the returned reviews to a given clinic,
        by filtering against a `clinic_id` query parameter in the URL.
        """
        queryset = self.queryset
        clinic_id = self.request.query_params.get('clinic_id', None)

        if clinic_id is not None:
            queryset = queryset.filter(clinic_id=clinic_id)

        return queryset

    def perform_create(self, serializer):
        clinic_id = self.request.data.get('clinic_id')

        if not clinic_id:
            raise serializers.ValidationError({'clinic_id': 'Clinic ID is required.'})

        try:
            clinic = Clinic.objects.get(id=clinic_id)

            # Check if user has already reviewed this clinic
            if ClinicReview.objects.filter(clinic=clinic, user=self.request.user).exists():
                raise serializers.ValidationError({'detail': 'You have already reviewed this clinic.'})

            serializer.save(clinic=clinic, user=self.request.user)
        except Clinic.DoesNotExist:
            raise serializers.ValidationError({'clinic_id': 'Clinic not found.'})

    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """
        Get all reviews made by the authenticated user.
        """
        reviews = ClinicReview.objects.filter(user=request.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)