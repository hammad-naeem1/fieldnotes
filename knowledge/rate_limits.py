from functools import wraps
import hashlib
import hmac
import time

from django.conf import settings
from django.db import transaction
from django.shortcuts import render
from django.db.models import F

from .models import RateLimitBucket


def rate_limit(action, limit, window_seconds):
    """Apply a database-backed per-IP limit to a view's POST requests."""
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.method == "POST":
                remote_ip = request.META.get(getattr(settings, "RATE_LIMIT_IP_HEADER", "REMOTE_ADDR"), "unknown")
                if "," in remote_ip:
                    remote_ip = remote_ip.split(",", 1)[0].strip()
                digest = hmac.new(
                    settings.SECRET_KEY.encode(),
                    f"{action}:{remote_ip}".encode(),
                    hashlib.sha256,
                ).hexdigest()
                window = int(time.time() // window_seconds)
                with transaction.atomic():
                    bucket, _ = RateLimitBucket.objects.get_or_create(
                        action=action,
                        key_hash=digest,
                        window=window,
                        defaults={"hits": 0},
                    )
                    RateLimitBucket.objects.filter(pk=bucket.pk).update(hits=F("hits") + 1)
                    bucket.refresh_from_db(fields=["hits"])
                if bucket.hits > limit:
                    return render(request, "errors/429.html", status=429)
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
