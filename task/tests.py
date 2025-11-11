from rest_framework.test import APITestCase
from rest_framework import status
from .models import Task, Project
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


class TaskSerializerTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='password')
        self.project = Project.objects.create(name='test_project', description='test')
        self.task = Task.objects.create(title='test_task',
                                        description='test description',
                                        priority=1, user=self.user,
                                        project=self.project)
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

    def test_task_serializer(self):
        response = self.client.get('/tasks/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('duration', response.data[0])
        self.assertEqual(response.data[0]['project']['name'], self.project.name)