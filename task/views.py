from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import filters
from .pagination import RoleBasePagination
from .serializers import TaskSerializer, ProjectSerializer
from .models import Task, Project
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from django.db import transaction
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .permissions import RoleBasedPermission, IsManagerOrStaff, ReadonlyOrAuthenticated
from .filters import  TaskFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User

import logging

logger = logging.getLogger(__name__)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    pagination_class = RoleBasePagination

    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter,
                       filters.OrderingFilter,)

    filterset_class = TaskFilter

    search_fields = ["title", "description"]

    ordering_fields = ["-priority", "due_date"]

    ordering = ("-priority")

    def get_queryset(self):
        user = self.request.user

        if user.groups.filter(name='manager').exists() or user.is_staff:
            qs = Task.objects.all()
        else:
            qs = Task.objects.filter(user=user)


    def perform_create(self, serializer):
        task = serializer.save(user=self.request.user)
        task.current_user = self.request.user
        task.save()

    def perform_update(self, serializer):
        task = serializer.save()
        task.current_user = self.request.user
        task.save()

    @action(detail=True, methods=['post'])
    def mark_done(self, request, pk=None):
        task = self.get_object()
        task.done = True
        task.current_user = self.request.user
        task.save()
        return Response({'status': 'success',
                         'message': 'Task marked as done',
                         'task': TaskSerializer(task).data})

    @action(detail=False, methods=['delete'])
    def delete_all_done(self, request, pk=None):
        user = request.user
        with transaction.atomic():
            tasks_to_delete = Task.objects.filter(done=True)
            for task in tasks_to_delete:
                task.current_user = user
                task.save()
            deleted_count, _ = Task.objects.filter(done=True).delete()

        logger.info(f"🧹 BULK DELETE - User: {user.username}, Deleted {deleted_count} done tasks")

        return Response({'status': 'success',
                         'deleted_count': deleted_count,
                         'message': 'Task deleted successfully'})

    @action(detail=False, methods=['get'])
    def my_stats(self, request):
        user = self.request.user
        tasks = Task.objects.filter(user=user)
        data = {
            'total': tasks.count(),
            'done': tasks.filter(done=True).count(),
            'pending': tasks.filter(done=False).count(),
        }
        return Response({
            'username': user.username,
            'task_summery': data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrStaff])
    def assign(self, request, pk=None):
        task = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'status': 'fail',
                             'detail': 'user_id is required'
                             }, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'status': 'fail',
                             'detail': 'User not found'
                             }, status=status.HTTP_404_NOT_FOUND)

        task.user = new_user
        task.save()

        return Response({"detail": f"Task assigned to user {new_user.username}"}, status=status.HTTP_200_OK)

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()
    permission_classes = [ReadonlyOrAuthenticated]

class CompletedTaskViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user, done=True)
