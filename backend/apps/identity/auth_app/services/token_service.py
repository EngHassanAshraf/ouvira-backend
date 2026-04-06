"""
Token Service - Handles JWT token generation and management
"""
import logging
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from apps.identity.account.models.user import CustomUser

logger = logging.getLogger(__name__)


class TokenService:
    """Service for JWT token operations"""

    @staticmethod
    def generate_tokens(user: CustomUser, remember_me: bool = False) -> dict:
        """
        Generate access and refresh tokens for a user.
        
        Args:
            user: User instance
            remember_me: Whether to extend token lifetime
            
        Returns:
            Dictionary with access, refresh tokens and expiry info
        """
        refresh = RefreshToken.for_user(user)
        
        if remember_me:
            # Extend access token lifetime for remember me — max 7 days (AUTH-003)
            refresh.access_token.set_exp(lifetime=timedelta(days=7))
            logger.warning("Long-lived token issued (remember_me) | user_id=%s", user.pk)
        
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "expires_in": 3600,  # 1 hour in seconds
        }

    @staticmethod
    def refresh_access_token(refresh_token_str: str) -> dict:
        """
        Generate a new access token from a refresh token.
        
        Args:
            refresh_token_str: Refresh token string
            
        Returns:
            Dictionary with new access token and expiry info
            
        Raises:
            TokenError: If refresh token is invalid
        """
        try:
            token = RefreshToken(refresh_token_str)
            return {
                "access": str(token.access_token),
                "expires_in": 3600,
            }
        except TokenError as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise

    @staticmethod
    def blacklist_token(refresh_token_str: str) -> bool:
        """
        Blacklist a refresh token (logout).
        
        Args:
            refresh_token_str: Refresh token string to blacklist
            
        Returns:
            True if successful, False otherwise
        """
        try:
            token = RefreshToken(refresh_token_str)
            token.blacklist()
            logger.info("Token blacklisted successfully")
            return True
        except TokenError as e:
            logger.error(f"Token blacklist error: {str(e)}")
            return False
