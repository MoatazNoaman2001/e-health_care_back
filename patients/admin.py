from django.contrib import admin
from .models import Patient, PatientAddress, MedicalHistory, Medication, FamilyMedicalHistory


class PatientAddressInline(admin.TabularInline):
    model = PatientAddress
    extra = 0


class MedicalHistoryInline(admin.TabularInline):
    model = MedicalHistory
    extra = 0
    fields = ('condition', 'diagnosis_date', 'is_current')


class MedicationInline(admin.TabularInline):
    model = Medication
    extra = 0
    fields = ('name', 'dosage', 'frequency', 'start_date', 'end_date', 'is_current')


class FamilyMedicalHistoryInline(admin.TabularInline):
    model = FamilyMedicalHistory
    extra = 0
    fields = ('relationship', 'condition', 'age_at_diagnosis')


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'get_email', 'date_of_birth', 'gender', 'is_insured', 'created_at')
    list_filter = ('gender', 'blood_type', 'is_insured', 'created_at')
    search_fields = ('first_name', 'last_name', 'user__email')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'gender', 'blood_type',
                       'height', 'weight', 'allergies')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship')
        }),
        ('Insurance Information', {
            'fields': ('is_insured', 'insurance_provider', 'insurance_policy_number', 'insurance_expiry_date')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PatientAddressInline, MedicalHistoryInline, MedicationInline, FamilyMedicalHistoryInline]

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'


@admin.register(PatientAddress)
class PatientAddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'address_type', 'city', 'state', 'is_primary')
    list_filter = ('address_type', 'is_primary', 'state', 'country')
    search_fields = ('patient__first_name', 'patient__last_name', 'street_address', 'city')

    fieldsets = (
        ('Patient', {
            'fields': ('patient',)
        }),
        ('Address Information', {
            'fields': ('street_address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Address Settings', {
            'fields': ('address_type', 'is_primary')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'condition', 'diagnosis_date', 'is_current')
    list_filter = ('is_current', 'diagnosis_date')
    search_fields = ('patient__first_name', 'patient__last_name', 'condition', 'treatment')
    date_hierarchy = 'diagnosis_date'

    fieldsets = (
        ('Patient', {
            'fields': ('patient',)
        }),
        ('Condition Information', {
            'fields': ('condition', 'diagnosis_date', 'is_current')
        }),
        ('Treatment Details', {
            'fields': ('treatment', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'name', 'dosage', 'frequency', 'start_date', 'is_current')
    list_filter = ('is_current', 'start_date', 'end_date')
    search_fields = ('patient__first_name', 'patient__last_name', 'name', 'prescribing_doctor')
    date_hierarchy = 'start_date'

    fieldsets = (
        ('Patient', {
            'fields': ('patient',)
        }),
        ('Medication Information', {
            'fields': ('name', 'dosage', 'frequency', 'prescribing_doctor')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'is_current')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(FamilyMedicalHistory)
class FamilyMedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'relationship', 'condition', 'age_at_diagnosis')
    list_filter = ('relationship',)
    search_fields = ('patient__first_name', 'patient__last_name', 'relationship', 'condition')

    fieldsets = (
        ('Patient', {
            'fields': ('patient',)
        }),
        ('Relationship and Condition', {
            'fields': ('relationship', 'condition', 'age_at_diagnosis')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')