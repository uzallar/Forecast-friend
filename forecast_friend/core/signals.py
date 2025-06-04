from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Country, SeasonalVisit
from django.core.cache import cache


@receiver([post_save, post_delete], sender=Country)
def clear_country_cache_on_change(sender, instance, **kwargs):
    cache_key = f"country_chart_{instance.id}"
    cache.delete(cache_key)


@receiver([post_save, post_delete], sender=SeasonalVisit)
def clear_country_cache_on_seasonalvisit_change(sender, instance, **kwargs):
    cache_key = f"country_chart_{instance.country.id}"
    cache.delete(cache_key)
