"""
Service utilities
"""

from apps.audit.services import ActivityLogService


def log_activity(user, action, resource_type, resource_id=None, details=None):
    """
    Wrapper for ActivityLogService
    TODO: Implement proper activity logging
    """
    try:
        # ActivityLogService.log(...)  # Implement when needed
        pass
    except Exception:
        pass  # Don't fail if logging fails