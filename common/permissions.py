from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to access it.
    """

    def has_object_permission(self, request, view, obj):
        # Check if the object has a user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # Check if the object has an owner attribute
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        return False


class IsPatient(permissions.BasePermission):
    """
    Permission to only allow patients to access the view.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'patient')


class IsDoctor(permissions.BasePermission):
    """
    Permission to only allow doctors to access the view.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'doctor')


class IsAdmin(permissions.BasePermission):
    """
    Permission to only allow admins to access the view.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


class ReadOnly(permissions.BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS