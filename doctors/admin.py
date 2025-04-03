from django.contrib import admin
from .models import (
    Doctor, Specialization, DoctorEducation, DoctorWorkExperience,
    DoctorCertification, InsuranceProvider, DoctorInsurance
)


class DoctorEducationInline(admin.StackedInline):
    model = DoctorEducation
    extra = 0


class DoctorWorkExperienceInline(admin.StackedInline):
    model = DoctorWorkExperience
    extra = 0


class DoctorCertificationInline(admin.TabularInline):
    model = DoctorCertification
    extra = 0


class DoctorInsuranceInline(admin.TabularInline):
    model = DoctorInsurance
    extra = 0


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'get_email', 'get_specializations', 'license_number', 'status')
    list_filter = ('status', 'specializations', 'accepts_insurance', 'video_consultation', 'home_visit')
    search_fields = ('first_name', 'last_name', 'user__email', 'license_number')
    filter_horizontal = ('specializations',)

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'title', 'profile_image')
        }),
        ('Professional Information', {
            'fields': ('specializations', 'license_number', 'years_of_experience', 'status')
        }),
        ('Profile Information', {
            'fields': ('bio', 'education', 'work_experience', 'languages')
        }),
        ('Practice Information', {
            'fields': ('consultation_fee', 'avg_rating', 'total_reviews', 'accepts_insurance',
                       'video_consultation', 'home_visit')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'avg_rating', 'total_reviews')
    inlines = [DoctorEducationInline, DoctorWorkExperienceInline, DoctorCertificationInline, DoctorInsuranceInline]

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'

    def get_specializations(self, obj):
        return ", ".join([str(s) for s in obj.specializations.all()])

    get_specializations.short_description = 'Specializations'


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'doctor_count')
    search_fields = ('name',)

    def doctor_count(self, obj):
        return obj.doctors.count()

    doctor_count.short_description = 'Number of Doctors'


@admin.register(DoctorEducation)
class DoctorEducationAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'degree', 'institution', 'start_year', 'end_year', 'is_current')
    list_filter = ('is_current', 'start_year', 'end_year')
    search_fields = ('doctor__first_name', 'doctor__last_name', 'degree', 'institution')


@admin.register(DoctorWorkExperience)
class DoctorWorkExperienceAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'position', 'institution', 'start_year', 'end_year', 'is_current')
    list_filter = ('is_current', 'start_year', 'end_year')
    search_fields = ('doctor__first_name', 'doctor__last_name', 'position', 'institution')


@admin.register(DoctorCertification)
class DoctorCertificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'name', 'organization', 'issue_date', 'expiry_date')
    list_filter = ('issue_date', 'expiry_date')
    search_fields = ('doctor__first_name', 'doctor__last_name', 'name', 'organization')


@admin.register(InsuranceProvider)
class InsuranceProviderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'website')
    search_fields = ('name',)


@admin.register(DoctorInsurance)
class DoctorInsuranceAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'insurance')
    list_filter = ('insurance',)
    search_fields = ('doctor__first_name', 'doctor__last_name', 'insurance__name')