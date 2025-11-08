from rest_framework import serializers
from .models import Task
from datetime import datetime


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'priority', 'done', 'created_at', 'due_date']

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

    def validate_priority(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError('Task priority must be between 1 and 10')
        return value

    def validate(self, data):
        current_time = datetime.now()
        done = data.get('done', False)
        due_date = data.get('due_date', None)

        if done == True and due_date > current_time:
            raise serializers.ValidationError('Due date must be after current time')
        return data