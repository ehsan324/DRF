from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Task
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Task)
def log_task_change(sender, instance, created, **kwargs):
    action = 'created' if created else 'updated'
    user = instance.user.username if instance.user else 'Unknown'
    logger.info(f"Task {instance.title} {action} by {user}")

@receiver(post_delete, sender=Task)
def log_task_delete(sender, instance, **kwargs):
    user = instance.user.username if instance.user else 'Unknown'
    logger.info(f"Task {instance.title} {action} by {user}")

