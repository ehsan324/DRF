from rest_framework import serializers
from .models import Task, Project
from django.utils import timezone
from drf_writable_nested import WritableNestedModelSerializer


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'created_at']

class TaskSerializer(WritableNestedModelSerializer):
    project = ProjectSerializer()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'priority', 'done', 'created_at', 'due_date', 'project', 'duration']

    def get_duration(self, obj):
        if obj.due_date and obj.done:
            duration = obj.due_date - obj.created_at.date()
            return duration.days
        return None

    def validate_title(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError('Task title must have at least 3 characters')
        if "error" in value.lower():
            raise serializers.ValidationError('Invalid task title')
        user = self.context['request'].user
        if Task.objects.filter(user=user, title=value).exists():
            raise serializers.ValidationError('Task with this title already exists')
        return value


    def validate(self, data):
        current_date = timezone.now().date()
        done = data.get('done', False)
        due_date = data.get('due_date', None)

        if done == True and due_date > current_date:
            raise serializers.ValidationError('Due date must be after current time')
        return data