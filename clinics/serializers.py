from rest_framework import serializers
from doctors.serializers import DoctorSerializer, InsuranceProviderSerializer
from accounts.serializers import UserSerializer
from .models import (
    Clinic, ClinicGallery, DoctorClinic, ClinicBusinessHours,
    ClinicSpecialty, ClinicInsurance, ClinicReview
)
from doctors.models import InsuranceProvider, Doctor


class ClinicGallerySerializer(serializers.ModelSerializer):
    """
    Serializer for the ClinicGallery model.
    """

    class Meta:
        model = ClinicGallery
        fields = ['id', 'image', 'caption', 'is_featured', 'created_at']
        read_only_fields = ['id', 'created_at']


class ClinicBusinessHoursSerializer(serializers.ModelSerializer):
    """
    Serializer for the ClinicBusinessHours model.
    """
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = ClinicBusinessHours
        fields = ['id', 'day_of_week', 'day_name', 'opening_time', 'closing_time', 'is_closed']
        read_only_fields = ['id']


class ClinicSpecialtySerializer(serializers.ModelSerializer):
    """
    Serializer for the ClinicSpecialty model.
    """

    class Meta:
        model = ClinicSpecialty
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


class ClinicInsuranceSerializer(serializers.ModelSerializer):
    """
    Serializer for the ClinicInsurance model.
    """
    insurance = InsuranceProviderSerializer(read_only=True)
    insurance_id = serializers.PrimaryKeyRelatedField(
        source='insurance',
        queryset=InsuranceProvider.objects.all(),
        write_only=True
    )

    class Meta:
        model = ClinicInsurance
        fields = ['id', 'insurance', 'insurance_id']
        read_only_fields = ['id']


class ClinicReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for the ClinicReview model.
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = ClinicReview
        fields = ['id', 'user', 'rating', 'title', 'review', 'is_verified', 'created_at']
        read_only_fields = ['id', 'user', 'is_verified', 'created_at']


class DoctorClinicSerializer(serializers.ModelSerializer):
    """
    Serializer for the DoctorClinic model.
    """
    doctor = DoctorSerializer(read_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(
        source='doctor',
        queryset=Doctor.objects.all(),
        write_only=True
    )

    class Meta:
        model = DoctorClinic
        fields = ['id', 'doctor', 'doctor_id', 'is_primary', 'created_at']
        read_only_fields = ['id', 'created_at']


class ClinicSerializer(serializers.ModelSerializer):
    """
    Serializer for the Clinic model.
    """

    class Meta:
        model = Clinic
        fields = [
            'id', 'name', 'clinic_type', 'address', 'city', 'state',
            'postal_code', 'country', 'phone_number', 'email', 'website',
            'description', 'services', 'facilities', 'established_year',
            'is_active', 'latitude', 'longitude', 'logo', 'featured_image',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClinicDetailSerializer(ClinicSerializer):
    """
    Detailed serializer for Clinic including related data.
    """
    gallery = ClinicGallerySerializer(many=True, read_only=True)
    business_hours = ClinicBusinessHoursSerializer(many=True, read_only=True)
    specialties = ClinicSpecialtySerializer(many=True, read_only=True)
    accepted_insurances = ClinicInsuranceSerializer(many=True, read_only=True)
    reviews = ClinicReviewSerializer(many=True, read_only=True)
    doctors = DoctorClinicSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta(ClinicSerializer.Meta):
        fields = ClinicSerializer.Meta.fields + [
            'gallery', 'business_hours', 'specialties', 'accepted_insurances',
            'reviews', 'doctors', 'average_rating', 'review_count'
        ]

    def get_average_rating(self, obj):
        """
        Calculate the average rating for the clinic.
        """
        reviews = obj.reviews.all()
        if not reviews:
            return None
        total = sum(review.rating for review in reviews)
        return round(total / reviews.count(), 1)

    def get_review_count(self, obj):
        """
        Count the number of reviews for the clinic.
        """
        return obj.reviews.count()


class ClinicRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new clinic.
    """
    business_hours = ClinicBusinessHoursSerializer(many=True, required=False)
    specialties = ClinicSpecialtySerializer(many=True, required=False)

    class Meta:
        model = Clinic
        fields = [
            'name', 'clinic_type', 'address', 'city', 'state',
            'postal_code', 'country', 'phone_number', 'email', 'website',
            'description', 'services', 'facilities', 'established_year',
            'latitude', 'longitude', 'logo', 'featured_image',
            'business_hours', 'specialties'
        ]

    def create(self, validated_data):
        """
        Create a new clinic with related business hours and specialties.
        """
        business_hours_data = validated_data.pop('business_hours', [])
        specialties_data = validated_data.pop('specialties', [])

        # Create clinic
        clinic = Clinic.objects.create(**validated_data)

        # Create business hours
        for hours_data in business_hours_data:
            ClinicBusinessHours.objects.create(clinic=clinic, **hours_data)

        # Create specialties
        for specialty_data in specialties_data:
            ClinicSpecialty.objects.create(clinic=clinic, **specialty_data)

        return clinic