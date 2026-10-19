from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import User
from .services import purge_user_ranking_data


@receiver(pre_delete, sender=User)
def remove_user_ranking_on_delete(sender, instance, **kwargs):
    purge_user_ranking_data(instance)
