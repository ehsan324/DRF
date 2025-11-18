import django_filters
from django.utils import timezone
from .models import Task
from datetime import timedelta
from django.db.models import Q


# logging
import logging
logger = logging.getLogger(__name__)


class TaskFilter(django_filters.FilterSet):

    due_after = django_filters.BooleanFilter(field_name='due_date', lookup_expr='gte')
    due_before = django_filters.BooleanFilter(field_name='due_date', lookup_expr='lte')
    urgent = django_filters.BooleanFilter(method='filter_urgent')
    has_due_date = django_filters.BooleanFilter(method='filter_has_due_date')

    q = django_filters.CharFilter(method='filter_q')




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

    def filter_q(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(due_date__icontains=value)
        )

