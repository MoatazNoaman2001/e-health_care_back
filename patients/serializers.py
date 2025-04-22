from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import Patient, PatientAddress, MedicalHistory, Medication, FamilyMedicalHistory


class PatientAddressSerializer(serializers.ModelSerializer):
    """
    Serializer for PatientAddress model.
    """

    class Meta:
        model = PatientAddress
        fields = ['id', 'street_address', 'city', 'state', 'postal_code',
                  'country', 'is_primary', 'address_type', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class MedicalHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for MedicalHistory model.
    """

    class Meta:
        model = MedicalHistory
        fields = ['id', 'condition', 'diagnosis_date', 'treatment',
                  'is_current', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class MedicationSerializer(serializers.ModelSerializer):
    """
    Serializer for Medication model.
    """

    class Meta:
        model = Medication
        fields = ['id', 'name', 'dosage', 'frequency', 'start_date',
                  'end_date', 'prescribing_doctor', 'is_current',
                  'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class FamilyMedicalHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for FamilyMedicalHistory model.
    """

    class Meta:
        model = FamilyMedicalHistory
        fields = ['id', 'relationship', 'condition', 'age_at_diagnosis',
                  'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PatientSerializer(serializers.ModelSerializer):
    """
    Serializer for the Patient model.
    """
    user = UserSerializer(read_only=True)
    age = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'user', 'first_name', 'last_name', 'date_of_birth',
                  'gender', 'blood_type', 'height', 'weight', 'allergies',
                  'emergency_contact_name', 'emergency_contact_phone',
                  'emergency_contact_relationship', 'is_insured',
                  'insurance_provider', 'insurance_policy_number',
                  'insurance_expiry_date', 'notes', 'age', 'full_name',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class PatientDetailSerializer(PatientSerializer):
    """
    Detailed serializer for Patient including related data.
    """
    addresses = PatientAddressSerializer(many=True, read_only=True)
    medical_history = MedicalHistorySerializer(many=True, read_only=True)
    medications = MedicationSerializer(many=True, read_only=True)
    family_medical_history = FamilyMedicalHistorySerializer(many=True, read_only=True)

    class Meta(PatientSerializer.Meta):
        fields = PatientSerializer.Meta.fields + ['addresses', 'medical_history',
                                                  'medications', 'family_medical_history']


class PatientRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new patient with user account.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = Patient
        fields = ['email', 'password', 'first_name', 'last_name', 'date_of_birth',
                  'gender', 'blood_type', 'height', 'weight', 'allergies',
                  'emergency_contact_name', 'emergency_contact_phone',
                  'emergency_contact_relationship', 'is_insured',
                  'insurance_provider', 'insurance_policy_number',
                  'insurance_expiry_date', 'notes']

    def create(self, validated_data):
        """
        Create a new patient with a user account.
        """
        from accounts.models import User

        email = validated_data.pop('email')
        password = validated_data.pop('password')

        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            user_type=User.UserType.PATIENT,
        )

        # Create patient profile
        patient = Patient.objects.create(user=user, **validated_data)

        return patient