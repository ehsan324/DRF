from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        view = context.get('view')
        request = context.get('request')

        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            response.data = {
                'status': 'error',
                'message': 'Authentication required. Please log in.',
                'code': 'authentication_required'
            }
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            user = request.user if request else None

            if user and user.is_authenticated:
                message = 'Your account does not have permission.'
                if user.groups.filter(name='manager').exists():
                    message += 'Manager have read-only access.'
            else:
                message = 'Authentication credentials were not provided.'

            response.data = {
                'status': 'error',
                'message': message,
                'code': 'permission_denied',
                'user_authenticated': user.is_authenticated if user else False,
                'user_role': 'manager' if user.groups.filter(name='manager').exists() else 'regular_user'
            }

            return response
