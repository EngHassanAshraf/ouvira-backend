"""
InternalTokenService
====================
Generates enriched JWT tokens for internal (employee) logins.

The access token payload includes:
  - user_id
  - company_id
  - employee_id (nullable)
  - roles (list)
  - permissions (list of permission codes)
  - modules (list of accessible module names)
  - token_type = "internal_access"

Uses SimpleJWT's RefreshToken as the base so blacklisting and rotation
work identically to the external auth flow.
"""
import logging
from typing import Optional

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

logger = logging.getLogger(__name__)


class InternalTokenService:

    @staticmethod
    def generate_tokens(
        user,
        company_id: int,
        employee_id: Optional[str],
        roles: list[str],
        permissions: list[str],
        modules: list[str],
    ) -> dict:
        """
        Generate access + refresh tokens with enriched internal payload.

        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "token_type": "Bearer",
                "expires_in": 900,   # 15 min in seconds
            }
        """
        refresh = RefreshToken.for_user(user)

        # Enrich access token payload
        access = refresh.access_token
        access["token_type"] = "internal_access"
        access["company_id"] = company_id
        access["employee_id"] = employee_id
        access["roles"] = roles
        access["permissions"] = permissions
        access["modules"] = modules

        logger.info(
            "Internal tokens generated | user_id=%s company_id=%s roles=%s",
            user.pk, company_id, roles,
        )

        return {
            "access_token": str(access),
            "refresh_token": str(refresh),
            "token_type": "Bearer",
            "expires_in": 900,  # 15 minutes
        }

    @staticmethod
    def blacklist(refresh_token_str: str) -> bool:
        """Blacklist a refresh token (internal logout)."""
        try:
            token = RefreshToken(refresh_token_str)
            token.blacklist()
            logger.info("Internal refresh token blacklisted")
            return True
        except TokenError as exc:
            logger.warning("Internal token blacklist failed: %s", exc)
            return False
