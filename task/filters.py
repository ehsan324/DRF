import django_filters
from .models import Task

class TaskFilter(django_filters.FilterSet):
    min_due = django_filters.DateFilter(field_name='due_date', lookup_expr='gte')
    max_due = django_filters.DateFilter(field_name='due_date', lookup_expr='lte')
    title_startwith_a = django_filters.BooleanFilter(method="filter_title_startwith_a")
    is_overdue = django_filters.BooleanFilter(method="filter_overdue")

    def filter_title_startwith_a(self, queryset, name, value):
        if value:
            return queryset.filter(title__istartswith="a")
        else:
            return queryset

    def filter_overdue(self, queryset, name, value):
        if value:
            return queryset.filter(done=False, due_date__lte=timezone.now())
        return queryset

    class Meta:
        model = Task
        fields = {
            "project": ["exact"],
            "done": ["exact"],
            "description": ["icontains"],
            "title": ["icontains",],

        }
