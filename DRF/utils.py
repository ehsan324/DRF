from django.core.cache import cache
from task.models import Project
from DRF import settings

CACHE_TIMEOUT = getattr(settings, 'CACHE_TIMEOUT', 3600)

def get_user_projects(user, *, force_refresh=False):
    cache_key = f"user:{user.id}:projects"

    if force_refresh:
        projects = list(
            Project.objects.filter(user=user)
            .only("id", "name")
            .values("id", "name")
        )
        cache.set(cache_key, projects, CACHE_TIMEOUT)
        return projects

    projects = cache.get(cache_key)
    if projects is not None:
        return projects

    projects = list(
        Project.objects.filter(user=user)
        .only("id", "name")
        .values("id", "name")
    )
    cache.set(cache_key, projects, CACHE_TIMEOUT)
    return projects