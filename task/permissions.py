from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if obj.user == request.user:
            return True
        logger.warning(f"Unauthenticated user: {request.user}")
        print("unauthenticated")
        return False

