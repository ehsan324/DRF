from django.contrib import messages
from django.contrib import admin

from .models import Task


def mark_done(modeladmin, request, queryset):
    allowed_pks = []
    for obj in queryset:
        if modeladmin.has_change_permission(request, obj):
            allowed_pks.append(obj.pk)

    if not allowed_pks:
        modeladmin.message_user(request, 'no permission for change', level=messages.WARNING)
        return

    allowed_qs = queryset.filter(pk__in=allowed_pks)

    updated_count = allowed_qs.update(done=True)

    skipped = queryset.count() - updated_count

    if updated_count:
        modeladmin.message_user(
            request,
            f"{updated_count} tasks were marked as done",
            level=messages.SUCCESS
        )

    if skipped:
        modeladmin.message_user(
            request,
            f"{skipped} tasks were skipped",
            level=messages.WARNING
        )


mark_done.short_description = 'Mark tasks as done'
mark_done.allowed_permissions = ('change',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'done')
    list_filter = ('user', 'done')
    search_fields = ('title', 'description')
    actions = [mark_done]

    def has_module_permission(self, request):
        return request.user.is_staff


    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user

        if user.is_superuser:
            return qs

        if user.is_staff:
            return qs

        if user.groups.filter(name='manager').exists():
            return qs

        return qs.filter(user=user)

    def has_change_permission(self, request, obj=None):
        user = request.user
        if user.is_superuser:
            return True
        if user.groups.filter(name='manager').exists():
            return True
        if obj is None:
            return True
        return obj.user == user

    def has_delete_permission(self, request, obj=None):
        user = request.user
        if user.is_superuser:
            return True
        if user.groups.filter(name='manager').exists():
            return True
        if obj is None:
            return True
        return obj.user == user

    def get_readonly_fields(self, request, obj=None):
        user = request.user
        if user.groups.filter(name='employee').exists() and not user.is_superuser:
            return ('user',)
        return super().get_readonly_fields(request, obj)

    def save_model(self, request, obj, form, change):
        if request.user.groups.filter(name='employee').exists() and not change:
            obj.user = request.user
        super().save_model(request, obj, form, change)
