from rest_framework import permissions


class IsUserOwner(permissions.BasePermission):
    """
    Permission to only allow owners of an account to view or edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Instance must have a user attribute
        return obj == request.user


class IsVerified(permissions.BasePermission):
    """
    Permission to only allow verified users to access the view.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.email_verified


class IsActiveUser(permissions.BasePermission):
    """
    Permission to only allow active users to access the view.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active and request.user.profile_status == 'active'


class HasRequiredUserType(permissions.BasePermission):
    """
    Permission to only allow specific user types.
    """
    required_type = None

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == self.required_type


class IsPatientUser(HasRequiredUserType):
    """
    Permission to only allow patient users.
    """
    required_type = 'patient'


class IsDoctorUser(HasRequiredUserType):
    """
    Permission to only allow doctor users.
    """
    required_type = 'doctor'


class IsAdminUser(HasRequiredUserType):
    """
    Permission to only allow admin users.
    """
    required_type = 'admin'


class IsClinicStaffUser(HasRequiredUserType):
    """
    Permission to only allow clinic staff users.
    """
    required_type = 'clinic_staff'