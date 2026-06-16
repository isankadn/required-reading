from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .cache import clear_required_reading_cache
from .models import RequiredReadingDocument, RequiredReadingSettings


@receiver(post_save, sender=RequiredReadingSettings)
@receiver(post_delete, sender=RequiredReadingSettings)
@receiver(post_save, sender=RequiredReadingDocument)
@receiver(post_delete, sender=RequiredReadingDocument)
def clear_cache_on_required_reading_change(sender, **kwargs):
    clear_required_reading_cache()
