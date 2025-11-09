from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Task
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Task)
def log_task_changes(sender, instance, created, **kwargs):
    user = getattr(instance, 'user', None) or instance.user

    if created:
        logger.info(
            f"📝 TASK CREATED - ID: {instance.id}, "
            f"Title: '{instance.title}', "
            f"User: {user.username if user else 'Unknown'}, "
            f"Done: {instance.done}"
        )
    else:
        if hasattr(instance, '_changed_data'):
            changes = instance._changed_data
            if changes:
                logger.info(
                    f"✏️ TASK UPDATED - ID: {instance.id}, "
                    f"Title: '{instance.title}', "
                    f"User: {user.username if user else 'Unknown'}, "
                    f"Changes: {changes}"
                )

@receiver(post_delete, sender=Task)
def log_task_deletion(sender, instance, **kwargs):
    user = getattr(instance, '_current_user', None) or instance.user

    logger.warning(
        f"🗑️ TASK DELETED - ID: {instance.id}, "
        f"Title: '{instance.title}', "
        f"User: {user.username if user else 'Unknown'}"
    )