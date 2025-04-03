from django.contrib import admin
from .models import (
    Clinic, ClinicGallery, DoctorClinic, ClinicBusinessHours,
    ClinicSpecialty, ClinicInsurance, ClinicReview
)


class ClinicGalleryInline(admin.TabularInline):
    model = ClinicGallery
    extra = 1


class DoctorClinicInline(admin.TabularInline):
    model = DoctorClinic
    extra = 1


class ClinicBusinessHoursInline(admin.TabularInline):
    model = ClinicBusinessHours
    extra = 7  # One for each day of the week


class ClinicSpecialtyInline(admin.TabularInline):
    model = ClinicSpecialty
    extra = 1


class ClinicInsuranceInline(admin.TabularInline):
    model = ClinicInsurance
    extra = 1


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'clinic_type', 'city', 'state', 'phone_number', 'is_active')
    list_filter = ('clinic_type', 'is_active', 'city', 'state')
    search_fields = ('name', 'address', 'city', 'state', 'postal_code', 'phone_number', 'email')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'clinic_type', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country',
                       'phone_number', 'email', 'website')
        }),
        ('Details', {
            'fields': ('description', 'services', 'facilities', 'established_year')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Media', {
            'fields': ('logo', 'featured_image')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = [
        ClinicBusinessHoursInline, ClinicSpecialtyInline,
        ClinicInsuranceInline, DoctorClinicInline, ClinicGalleryInline
    ]


@admin.register(ClinicGallery)
class ClinicGalleryAdmin(admin.ModelAdmin):
    list_display = ('id', 'clinic', 'caption', 'is_featured')
    list_filter = ('is_featured', 'clinic')
    search_fields = ('clinic__name', 'caption')


@admin.register(DoctorClinic)
class DoctorClinicAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'clinic', 'is_primary')
    list_filter = ('is_primary', 'clinic')
    search_fields = ('doctor__first_name', 'doctor__last_name', 'clinic__name')


@admin.register(ClinicBusinessHours)
class ClinicBusinessHoursAdmin(admin.ModelAdmin):
    list_display = ('id', 'clinic', 'day_of_week', 'opening_time', 'closing_time', 'is_closed')
    list_filter = ('day_of_week', 'is_closed', 'clinic')
    search_fields = ('clinic__name',)


@admin.register(ClinicSpecialty)
class ClinicSpecialtyAdmin(admin.ModelAdmin):
    list_display = ('id', 'clinic', 'name')
    list_filter = ('clinic',)
    search_fields = ('clinic__name', 'name')


@admin.register(ClinicInsurance)
class ClinicInsuranceAdmin(admin.ModelAdmin):
    list_display = ('id', 'clinic', 'insurance')
    list_filter = ('clinic', 'insurance')
    search_fields = ('clinic__name', 'insurance__name')


@admin.register(ClinicReview)
class ClinicReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'clinic', 'user', 'rating', 'title', 'is_verified')
    list_filter = ('rating', 'is_verified', 'clinic')
    search_fields = ('clinic__name', 'user__email', 'title', 'review')
    readonly_fields = ('created_at', 'updated_at')