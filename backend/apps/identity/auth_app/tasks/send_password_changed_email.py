"""
Celery task: send security email after password change.

Uses django-ipware at call site (views.py) — this task receives only primitives.
Task signature accepts ONLY JSON-serializable primitives (user_id, ip, user_agent, timestamp).
Never accepts a User object, request object, or any Django model instance.
"""

import os
import logging
from datetime import datetime

import zoneinfo
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


import geoip2.database
import geoip2.errors


@shared_task(bind=True, max_retries=3)
def send_password_changed_email(self, user_id: int, ip: str, user_agent: str, timestamp: str):
    """
    All arguments are JSON-serializable primitives.
    Resolves user inside the task — never serializes the User object.

    Args:
        user_id:    CustomUser PK (int)
        ip:         IP address string (extracted via ipware at call site)
        user_agent: Raw User-Agent header string
        timestamp:  ISO-8601 UTC datetime string
    """
    try:
        from apps.identity.account.models.user import CustomUser

        user = CustomUser.objects.get(id=user_id)

        # Parse User-Agent
        device_info = _parse_user_agent(user_agent)

        # Resolve geo and timezone from IP
        location_info, tz_string = _resolve_geo(ip)

        # Parse timestamp (always UTC ISO from signal)
        dt_utc = datetime.fromisoformat(timestamp)
        if not dt_utc.tzinfo:
            dt_utc = dt_utc.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))

        # Localize time
        try:
            target_tz = zoneinfo.ZoneInfo(tz_string) if tz_string else zoneinfo.ZoneInfo("UTC")
            dt_local = dt_utc.astimezone(target_tz)
            formatted_time = dt_local.strftime("%Y-%m-%d %H:%M:%S")
            tz_label = f"{target_tz.key} ({dt_local.strftime('%z')})"
        except Exception:
            formatted_time = dt_utc.strftime("%Y-%m-%d %H:%M:%S")
            tz_label = "UTC"

        body = f"""Hi {user.full_name or user.username},

Your Ouvira password was recently changed with the following details:

  Device:   {device_info}
  Location: {location_info}
  IP:       {ip}
  Time:     {formatted_time} {tz_label}

If this was you, no action is needed.

If this was NOT you, please contact us immediately at security@ouvira.com
or secure your account by requesting a reset here: {settings.FRONTEND_URL}/forgot-password

— Ouvira Security Team
"""
        send_mail(
            subject="Your Ouvira password was changed",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info("Password-changed email sent | user_id=%s", user_id)

    except Exception as exc:
        logger.exception("Failed to send password-changed email | user_id=%s | attempt=%s",
                         user_id, self.request.retries + 1)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


def _parse_user_agent(user_agent: str) -> str:
    """Parse browser and OS from User-Agent string using the user-agents library."""
    try:
        import user_agents
        ua = user_agents.parse(user_agent)
        return f"{ua.browser.family} on {ua.os.family}"
    except Exception:
        return user_agent or "Unknown device"


def _resolve_geo(ip: str) -> tuple[str, str | None]:
    """Returns (location_string, timezone_string)"""
    try:
        db_path = getattr(settings, "GEOIP_PATH", None) or \
                  os.path.join(settings.BASE_DIR, "geoip", "GeoLite2-City.mmdb")
        with geoip2.database.Reader(db_path) as reader:
            response = reader.city(ip)
            city = response.city.name or "Unknown city"
            country = response.country.name or "Unknown country"
            tz = response.location.time_zone
            return f"{city}, {country}", tz
    except geoip2.errors.AddressNotFoundError:
        return "Location unavailable", None
    except Exception as e:
        logger.warning("GeoLite2 lookup failed for IP %s: %s", ip, e)
        return "Location unavailable", None
