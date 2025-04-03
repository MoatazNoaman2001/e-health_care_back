from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from ...accounts.views import UserViewSet
from ...patients.views import (
    PatientViewSet, PatientAddressViewSet, MedicalHistoryViewSet,
    MedicationViewSet, FamilyMedicalHistoryViewSet
)
from ...doctors.views import (
    DoctorViewSet, SpecializationViewSet, DoctorEducationViewSet,
    DoctorWorkExperienceViewSet, DoctorCertificationViewSet,
    InsuranceProviderViewSet
)
from ...clinics.views import (
    ClinicViewSet, ClinicGalleryViewSet, ClinicBusinessHoursViewSet,
    ClinicSpecialtyViewSet, ClinicReviewViewSet
)
from ...appointments.views import (
    AppointmentViewSet, AppointmentDocumentViewSet,
    MedicalRecordViewSet, AppointmentFeedbackViewSet,
    AppointmentReminderViewSet
)
from ...schedules.views import (
    ScheduleViewSet, ScheduleExceptionViewSet, TimeSlotViewSet,
    AvailabilityPreferenceViewSet
)

# Create a router for top-level resources
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'patients', PatientViewSet)
router.register(r'doctors', DoctorViewSet)
router.register(r'clinics', ClinicViewSet)
router.register(r'appointments', AppointmentViewSet)
router.register(r'specializations', SpecializationViewSet)
router.register(r'insurance-providers', InsuranceProviderViewSet)
router.register(r'schedules', ScheduleViewSet)
router.register(r'schedule-exceptions', ScheduleExceptionViewSet)
router.register(r'time-slots', TimeSlotViewSet)
router.register(r'availability-preferences', AvailabilityPreferenceViewSet)

# Create nested routers for patient resources
patients_router = routers.NestedSimpleRouter(router, r'patients', lookup='patient')
patients_router.register(r'addresses', PatientAddressViewSet, basename='patient-addresses')
patients_router.register(r'medical-history', MedicalHistoryViewSet, basename='patient-medical-history')
patients_router.register(r'medications', MedicationViewSet, basename='patient-medications')
patients_router.register(r'family-medical-history', FamilyMedicalHistoryViewSet, basename='patient-family-medical-history')
patients_router.register(r'appointments', AppointmentViewSet, basename='patient-appointments')

# Create nested routers for doctor resources
doctors_router = routers.NestedSimpleRouter(router, r'doctors', lookup='doctor')
doctors_router.register(r'education', DoctorEducationViewSet, basename='doctor-education')
doctors_router.register(r'work-experience', DoctorWorkExperienceViewSet, basename='doctor-work-experience')
doctors_router.register(r'certifications', DoctorCertificationViewSet, basename='doctor-certifications')
doctors_router.register(r'schedules', ScheduleViewSet, basename='doctor-schedules')
doctors_router.register(r'appointments', AppointmentViewSet, basename='doctor-appointments')
doctors_router.register(r'time-slots', TimeSlotViewSet, basename='doctor-time-slots')

# Create nested routers for clinic resources
clinics_router = routers.NestedSimpleRouter(router, r'clinics', lookup='clinic')
clinics_router.register(r'gallery', ClinicGalleryViewSet, basename='clinic-gallery')
clinics_router.register(r'business-hours', ClinicBusinessHoursViewSet, basename='clinic-business-hours')
clinics_router.register(r'specialties', ClinicSpecialtyViewSet, basename='clinic-specialties')
clinics_router.register(r'reviews', ClinicReviewViewSet, basename='clinic-reviews')
clinics_router.register(r'doctors', DoctorViewSet, basename='clinic-doctors')
clinics_router.register(r'appointments', AppointmentViewSet, basename='clinic-appointments')

# Create nested routers for appointment resources
appointments_router = routers.NestedSimpleRouter(router, r'appointments', lookup='appointment')
appointments_router.register(r'documents', AppointmentDocumentViewSet, basename='appointment-documents')
appointments_router.register(r'medical-records', MedicalRecordViewSet, basename='appointment-medical-records')
appointments_router.register(r'feedback', AppointmentFeedbackViewSet, basename='appointment-feedback')
appointments_router.register(r'reminders', AppointmentReminderViewSet, basename='appointment-reminders')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(patients_router.urls)),
    path('', include(doctors_router.urls)),
    path('', include(clinics_router.urls)),
    path('', include(appointments_router.urls)),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]