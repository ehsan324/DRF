from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)

class RoleBasedPermission(permissions.BasePermission):
    """
    Admin → full access
    Manager → read-only for all
    User → access only to own tasks
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        is_manager = user.groups.filter(name='manager').exists()

        if request.method == 'DELETE':
            return is_manager

        if request.method in ('PATCH', 'PUT'):
            if is_manager:
                return True
            return obj.user == user

        return False

class IsManagerOrStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        is_manager = user.groups.filter(name='manager').exists()
        return is_manager or user.is_staff

class ReadonlyOrAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated