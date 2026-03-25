"""
Shared password utility functions.

These are used by both PasswordResetService and PasswordChangeService
to avoid duplicating security-critical logic.
"""

from django.contrib.auth.hashers import check_password

from apps.identity.auth_app.models import PasswordHistory


def is_password_reused(user, new_password: str, limit: int = 5) -> bool:
    """
    Returns True if new_password matches any of the user's last `limit`
    password hashes stored in PasswordHistory.

    Uses Django's check_password so the comparison is bcrypt-aware
    and timing-safe (constant-time digest comparison internally).

    Args:
        user: CustomUser instance
        new_password: The candidate new password (plaintext)
        limit: How many historical hashes to check (default: 5)

    Returns:
        True if the password was recently used; False otherwise.
    """
    recent = (
        PasswordHistory.objects
        .filter(user=user)
        .order_by("-changed_at")[:limit]
    )
    return any(
        check_password(new_password, record.password_hash)
        for record in recent
    )
