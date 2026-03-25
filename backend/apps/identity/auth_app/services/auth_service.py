"""
Authentication Service - Handles user authentication, signup, and login logic
"""
import logging
from random import randint
from django.db import IntegrityError, DatabaseError
from django.utils import timezone
from django.contrib.auth import authenticate

from apps.identity.account.models.user import CustomUser
from apps.shared.exceptions import BusinessException
from apps.shared.messages.error import ERROR_MESSAGES
from .otp_service import OTPService

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication-related operations"""

    @staticmethod
    def generate_username(full_name: str) -> str:
        """Generate a unique username from full name"""
        base_username = full_name.replace(" ", "_").lower()
        random_suffix = str(randint(1000, 9999))
        return f"{base_username}{random_suffix}"

    @staticmethod
    def signup_user(phone_number: str, full_name: str) -> tuple[CustomUser, bool]:
        """
        Sign up a new user or get existing user.
        
        Args:
            phone_number: User's phone number
            full_name: User's full name
            
        Returns:
            Tuple of (user, created)
            
        Raises:
            IntegrityError: If user creation fails due to database constraints
        """
        try:
            user, created = CustomUser.objects.get_or_create(
                primary_mobile=phone_number,
                defaults={
                    "full_name": full_name,
                    "username": AuthService.generate_username(full_name),
                },
            )
            
            if created:
                logger.info("New user created | user_id=%s", user.pk)
            else:
                logger.info("Existing user retrieved | user_id=%s", user.pk)
            
            return user, created
            
        except IntegrityError as e:
            logger.error(f"Integrity error during signup for {phone_number}: {str(e)}")
            raise

    @staticmethod
    def verify_user_otp(identifier: str, otp_code: str):
        """
        Coordinates OTP verification and updates user state.
        Returns the user object on success.
        """
        channel = OTPService.verify(identifier, otp_code)

        user = AuthService.get_user_by_identifier(identifier)
        if user:
            if channel == "email":
                user.email_verified = True
                user.save(update_fields=["email_verified"])
            else:
                user.phone_verified = True
                user.save(update_fields=["phone_verified"])

        logger.info("User OTP verified | identifier=%s", identifier)
        return user

    @staticmethod
    def get_user_by_identifier(identifier: str) -> CustomUser | None:
        """
        Get user by username, email, or phone number.
        
        Args:
            identifier: Username, email, or phone number
            
        Returns:
            User instance or None
        """
        from django.db.models import Q
        
        return CustomUser.objects.filter(
            Q(username=identifier) | Q(email=identifier) | Q(primary_mobile=identifier)
        ).first()

    @staticmethod
    def authenticate_user(identifier: str, password: str) -> CustomUser | None:
        """
        Authenticate a user by identifier and password.
        
        Args:
            identifier: Username, email, or phone number
            password: User password
            
        Returns:
            User instance if authenticated, None otherwise
        """
        user = AuthService.get_user_by_identifier(identifier)
        
        if not user:
            return None
        
        # Check if account is locked
        if user.is_locked():
            logger.warning(f"Login attempt for locked account: {identifier}")
            return None
        
        # Verify password
        if not user.check_password(password):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.lock_account(minutes=30)
            else:
                user.save(update_fields=["failed_login_attempts"])
            return None
        
        # Reset failed login attempts on successful authentication
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.save(update_fields=["failed_login_attempts", "locked_until"])
        
        return user

    @staticmethod
    def finalize_signup(user: CustomUser, email: str, password: str) -> CustomUser:
        """
        Finalize user signup by setting email and password.
        
        Args:
            user: User instance
            email: User email
            password: User password
            
        Returns:
            Updated user instance
            
        Raises:
            BusinessException: If email already exists
        """
        # Check if email is already taken
        if CustomUser.objects.filter(email=email).exclude(pk=user.pk).exists():
            raise BusinessException("Email is already registered")
        
        user.email = email
        user.set_password(password)
        user.save(update_fields=["email", "password"])
        
        logger.info("Signup finalized | user_id=%s", user.pk)
        return user
