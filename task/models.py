from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='users')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TaskManager(models.Manager):
    def completed(self):
        return self.filter(done=True)

    def high_priority(self):
        return self.filter(priority__gte=3)


class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(db_index=True, max_length=100)
    description = models.TextField(blank=True)
    priority = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    due_date = models.DateField(null=True, blank=True)
    done = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.title} (priority={self.priority}) - {self.user.username}"

