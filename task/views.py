from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import filters

from DRF.utils import get_user_projects
from .pagination import RoleBasePagination
from .serializers import TaskListSerializer, ProjectSimpleSerializer, TaskDetailSerializer
from .models import Task, Project
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from django.db import transaction
from django.db.models import Q, Count
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .permissions import RoleBasedPermission, IsManagerOrStaff, ReadonlyOrAuthenticated
from .filters import TaskFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import logging

logger = logging.getLogger(__name__)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskDetailSerializer
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
            qs = Task.objects.select_related("user", "project")
        else:
            qs = Task.objects.filter(user=user)

        before_id = self.request.query_params.get('before_id', None)
        if before_id is not None:
            qs = qs.filter(id__lt=before_id)

        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        if self.action == 'retrieve':
            return TaskDetailSerializer
        return super().get_serializer_class()

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

    @method_decorator(cache_page(60 * 5))  ## 5 minutes set
    @action(detail=False, methods=['get'], permission_classes=[IsManagerOrStaff])
    def summery(self, request, pk=None):
        user = request.user

        if user.is_staff or user.groups.filter(name='manager').exists():
            qs = Task.objects.all()
        else:
            qs = Task.objects.filter(user=user)

        stats = qs.aggregate(
            completed=Count('id', filter=Q(done=True)),
            pending=Count('id', filter=Q(done=False))

        )
        return Response({
            'username': user.username,
            'stats': stats,
        })


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSimpleSerializer
    authentication_classes = [JWTAuthentication]
    queryset = Project.objects.all()
    permission_classes = [ReadonlyOrAuthenticated]

    @action(detail=False, methods=['get'])
    def my_cache_projects(self, request, pk=None):
        user = request.user
        refresh_param = request.query_params.get('refresh', None)
        force_refresh = refresh_param in ['true', '1', 'True']

        projects_data = get_user_projects(user, force_refresh=force_refresh)

        return Response({'projects': projects_data})

class CompletedTaskViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user, done=True)
