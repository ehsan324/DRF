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

        if user.is_staff:
            return True

        if user.groups.filter(name='manager').exists():
            return request.method in permissions.SAFE_METHODS

        return obj.user == user
