from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from knowledge.models import RateLimitBucket


class Command(BaseCommand):
    help = "Remove expired database-backed rate limit buckets."

    def handle(self, *args, **options):
        # Window values use per-action durations, so retain the model's current rows
        # only; older bucket records are trimmed by their creation time below.
        cutoff = timezone.now() - timedelta(days=2)
        deleted, _ = RateLimitBucket.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"Removed {deleted} expired rate limit record(s)."))
