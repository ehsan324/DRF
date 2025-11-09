from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from .serializers import TaskSerializer
from .models import Task
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view
from django.db import transaction
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .permissions import IsOwnerOrAdmin
from django.db.models import Case, When, IntegerField, Count


@api_view(['POST'])
@csrf_exempt
def LoginView(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None:
        login(request, user)
        return Response({
            'status': "success",
            'message': 'Successfully logged in.',
            'user_id': user.id,
            'username': user.username
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'status': "error",
            'message': 'Invalid credentials.',
        }, status=status.HTTP_401_UNAUTHORIZED)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Task.objects.all() if user.is_staff else Task.objects.filter(user=self.request.user)
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
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_done(self, request, pk=None):
        task = self.get_object()
        task.done = True
        task.save()
        return Response({'status': 'success',
                         'message': 'Task marked as done',
                         'task': TaskSerializer(task).data})

    @action(detail=False, methods=['delete'])
    def delete_all_done(self, request, pk=None):
        with transaction.atomic():
            deleted_count, _ = Task.objects.filter(done=True).delete()
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
