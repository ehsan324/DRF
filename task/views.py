from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework.response import Response
from .serializers import TaskSerializer
from .models import Task
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from django.db import transaction
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .permissions import RoleBasedPermission
import logging

logger = logging.getLogger(__name__)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, RoleBasedPermission]


    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            qs = Task.objects.all()
        elif user.groups.filter(name='manager').exists():
            qs = Task.objects.all()
        else:
            qs = Task.objects.filter(user=user)

        done = self.request.GET.get('done')
        search = self.request.GET.get('search')
        if done is not None:
            if done.lower() == 'true':
                qs = qs.filter(done=True)
            elif done.lower() == 'false':
                qs = qs.filter(done=False)
        if search:
            qs = qs.filter(title__icontains=search)
        return qs

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


class CompletedTaskViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user, done=True)
