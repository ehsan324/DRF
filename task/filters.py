import django_filters
from django.utils import timezone
from .models import Task
from datetime import timedelta

# logging
import logging
logger = logging.getLogger(__name__)


class TaskFilter(django_filters.FilterSet):
    urgent = django_filters.BooleanFilter(method='filter_urgent')
    has_due_date = django_filters.BooleanFilter(method='filter_has_due_date')



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

    def filter_has_due_date(self, queryset, name, value):
        if value is True:
            return queryset.exclude(due_date__isnull=True)
        if value is False:
            return queryset.filter(due_date__isnull=True)
        return queryset