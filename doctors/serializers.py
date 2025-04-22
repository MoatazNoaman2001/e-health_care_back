from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import (
    Doctor, Specialization, DoctorEducation, DoctorWorkExperience,
    DoctorCertification, InsuranceProvider, DoctorInsurance
)


class SpecializationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Specialization model.
    """

    class Meta:
        model = Specialization
        fields = ['id', 'name', 'description']


class DoctorEducationSerializer(serializers.ModelSerializer):
    """
    Serializer for the DoctorEducation model.
    """

    class Meta:
        model = DoctorEducation
        fields = ['id', 'degree', 'institution', 'location', 'start_year',
                  'end_year', 'is_current', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DoctorWorkExperienceSerializer(serializers.ModelSerializer):
    """
    Serializer for the DoctorWorkExperience model.
    """

    class Meta:
        model = DoctorWorkExperience
        fields = ['id', 'institution', 'position', 'location', 'description',
                  'start_year', 'end_year', 'is_current', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DoctorCertificationSerializer(serializers.ModelSerializer):
    """
    Serializer for the DoctorCertification model.
    """

    class Meta:
        model = DoctorCertification
        fields = ['id', 'name', 'organization', 'issue_date', 'expiry_date',
                  'certificate_number', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class InsuranceProviderSerializer(serializers.ModelSerializer):
    """
    Serializer for the InsuranceProvider model.
    """

    class Meta:
        model = InsuranceProvider
        fields = ['id', 'name', 'description', 'website']


class DoctorInsuranceSerializer(serializers.ModelSerializer):
    """
    Serializer for the DoctorInsurance model.
    """
    insurance = InsuranceProviderSerializer(read_only=True)
    insurance_id = serializers.PrimaryKeyRelatedField(
        queryset=InsuranceProvider.objects.all(),
        source='insurance',
        write_only=True
    )

    class Meta:
        model = DoctorInsurance
        fields = ['id', 'insurance', 'insurance_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DoctorSerializer(serializers.ModelSerializer):
    """
    Serializer for the Doctor model.
    """
    user = UserSerializer(read_only=True)
    specializations = SpecializationSerializer(many=True, read_only=True)
    specialization_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Specialization.objects.all(),
        source='specializations',
        write_only=True,
        required=False
    )
    full_name = serializers.CharField(read_only=True)
    specializations_list = serializers.ListField(read_only=True)

    class Meta:
        model = Doctor
        fields = [
            'id', 'user', 'first_name', 'last_name', 'title', 'full_name',
            'specializations', 'specialization_ids', 'specializations_list',
            'license_number', 'years_of_experience', 'status', 'bio',
            'education', 'work_experience', 'languages', 'consultation_fee',
            'avg_rating', 'total_reviews', 'accepts_insurance', 'profile_image',
            'video_consultation', 'home_visit', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'avg_rating', 'total_reviews', 'created_at', 'updated_at']


class DoctorDetailSerializer(DoctorSerializer):
    """
    Detailed serializer for Doctor including related data.
    """
    education_details = DoctorEducationSerializer(many=True, read_only=True)
    work_experiences = DoctorWorkExperienceSerializer(many=True, read_only=True)
    certifications = DoctorCertificationSerializer(many=True, read_only=True)
    accepted_insurances = DoctorInsuranceSerializer(many=True, read_only=True)

    class Meta(DoctorSerializer.Meta):
        fields = DoctorSerializer.Meta.fields + [
            'education_details', 'work_experiences', 'certifications', 'accepted_insurances'
        ]


class DoctorRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new doctor with user account.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    specialization_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Specialization.objects.all(),
        write_only=True
    )

    class Meta:
        model = Doctor
        fields = [
            'email', 'password', 'first_name', 'last_name', 'title',
            'specialization_ids', 'license_number', 'years_of_experience',
            'bio', 'education', 'work_experience', 'languages', 'consultation_fee',
            'accepts_insurance', 'profile_image', 'video_consultation', 'home_visit'
        ]

    def create(self, validated_data):
        """
        Create a new doctor with a user account.
        """
        from accounts.models import User

        email = validated_data.pop('email')
        password = validated_data.pop('password')
        specializations = validated_data.pop('specialization_ids')

        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            user_type=User.UserType.DOCTOR,
        )

        # Create doctor profile
        doctor = Doctor.objects.create(user=user, **validated_data)

        # Add specializations
        doctor.specializations.set(specializations)

        return doctor