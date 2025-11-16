import django_filters
from django.utils import timezone
from .models import Task
from datetime import timedelta

# logging
import logging
logger = logging.getLogger(__name__)


class TaskFilter(django_filters.FilterSet):
    min_due = django_filters.DateFilter(field_name='due_date', lookup_expr='gte')
    max_due = django_filters.DateFilter(field_name='due_date', lookup_expr='lte')

    urgent = django_filters.BooleanFilter(method='filter_urgent')

    class Meta:
        model = Task
        fields = {
            "project": ["exact"],
            "done": ["exact"],
            "title": ["icontains"],
            "description": ["icontains"],
        }

    def filter_urgent(self, queryset, name, value):
        if value:
            now = timezone.now()
            limit = now + timedelta(hours=48)
            return queryset.filter(due_date__lte=limit,
                                   done=False,
                                   due_date__isnull=False)
        return queryset