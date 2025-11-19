from datetime import timezone

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Task


def get_task_list_url(self):
    return reverse("tasks-list")


def get_task_detail_url(self, pk):
    return reverse("tasks-detail", args=[pk])


def get_task_mark_done_url(self, pk):
    return reverse("tasks-mark-done", args=[pk])  # action(detail=True, name='mark_done')


def get_completed_task_list_url(self):
    return reverse("completed-tasks-list")


class BaseAPITestCase(APITestCase):
    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="testuser1",
            email="user1@gmail.com",
            password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="testuser2",
            email="user2@gmail.com",
            password="testpass123"
        )
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@gmail.com",
            password="testpass123"
        )

    def get_access_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def auth_as(self, user):
        token = self.get_access_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')


class TaskViewSetTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.task1 = Task.objects.create(
            user=self.user,
            title="Task 1",
            description="good description",
            done=False,
        )

        self.task2 = Task.objects.create(
            user=self.user,
            title="Task 2",
            description="nice description",
            done=True,
        )

        self.task3 = Task.objects.create(
            user=self.other_user,
            title="Other Task 3",
            description="other nice description",
            done=False,
        )

    def test_task_list_returns_only_current_user_tasks(self):
        self.auth_as(self.user)

        url = reverse('tasks-list')
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', response.data)

        self.assertEqual(len(results), 2)
        returned_titles = {item["title"] for item in results}
        self.assertIn(self.task1.title, returned_titles)
        self.assertIn(self.task2.title, returned_titles)
        self.assertIn(self.task3.title, returned_titles)

    def test_task_create_sets_user_automatically(self):
        self.auth_as(self.user)

        url = reverse('tasks-list')
        payload = {
            "title": "New Task",
            "description": "Test description",
            "done": True,
            "due_date": timezone.now(),
        }

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 4)

        task = Task.objects.get(title="New Task")
        self.assertEqual(task.user, self.user)

    def test_mark_done_action_marks_task_as_done(self):
        self.auth_as(self.user)

        self.assertFalse(self.task1.done)

        url = reverse("tasks-mark-done", args=[self.task1.pk])
        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task1.refresh_from_db()
        self.assertTrue(self.task1.done)

