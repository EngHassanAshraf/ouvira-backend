"""
Optimized serializers for authentication endpoints
"""
import re
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db.models import Q
from rest_framework import serializers

from apps.identity.account.models.user import CustomUser
from ..utils import validate_user_email, validate_user_password, validate_user_mobile, verify_turnstile

# ==================== BASE SERIALIZERS ====================

class BaseUserInputSerializer(serializers.Serializer):
    """Base serializer for user input validation"""
    full_name = serializers.CharField(
        min_length=3, 
        max_length=255, 
        allow_blank=False,
        help_text="User's full name (letters and spaces only)"
    )
    primary_mobile = serializers.CharField(
        max_length=13, 
        allow_blank=False,
        help_text="Phone number in format +CountryCodeXXXXXXXXX"
    )

    def validate_full_name(self, value):
        """Validate full name contains only letters and spaces"""
        if not re.match(r"^[A-Za-z\s]+$", value):
            raise serializers.ValidationError(
                "The name must contain only letters and spaces."
            )
        return value.strip()

    def validate_primary_mobile(self, value):
        """Validate phone number format and uniqueness"""
        try:
            validate_user_mobile(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        
        # Check uniqueness only for signup, not for existing users
        if self.context.get("check_uniqueness", True):
            if CustomUser.objects.filter(primary_mobile=value).exists():
                raise serializers.ValidationError("Phone number is already in use.")
        
        return value


# ==================== SIGNUP SERIALIZERS ====================

class SignupSerializer(BaseUserInputSerializer):
    """Serializer for user signup"""
    cf_turnstile_response = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        help_text="Cloudflare Turnstile token"
    )

    def validate(self, attrs):
        request = self.context.get("request")
        token = attrs.get("cf_turnstile_response")
        if not verify_turnstile(request, token):
            raise serializers.ValidationError({"cf_turnstile_response": "Invalid Turnstile token"})
        return attrs

class FinalizeSignInSerializer(serializers.Serializer):
    """Serializer for finalizing signup with email and password"""
    primary_mobile = serializers.CharField(
        max_length=13, 
        allow_blank=False,
        help_text="Phone number in format +CountryCodeXXXXXXXXX"
    )
    email = serializers.EmailField(
        max_length=255,
        allow_blank=False,
        help_text="Valid email address"
    )
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=40,
        help_text="Password: 8-40 chars, 1 uppercase, 1 lowercase, 1 number, 1 special char"
    )

    def validate_primary_mobile(self, value):
        """Validate phone number format"""
        try:
            validate_user_mobile(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate_email(self, value):
        """Validate email format and uniqueness"""
        value = value.strip().lower()
        
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already registered")
        
        try:
            validate_user_email(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        
        return value

    def validate_password(self, value):
        """Validate password strength"""
        try:
            validate_user_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value


# ==================== OTP SERIALIZERS ====================

class ResentOTPSerializer(serializers.Serializer):
    """Serializer for resending OTP"""
    primary_mobile = serializers.CharField(
        validators=[
            RegexValidator(
                regex=r"^\+20(10|11|12|15)\d{8}$",
                message="Phone number must be in the format +201XXXXXXXX (Egypt)"
            )
        ],
        help_text="Phone number to resend OTP to"
    )
    cf_turnstile_response = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        help_text="Cloudflare Turnstile token"
    )

    def validate(self, attrs):
        request = self.context.get("request")
        token = attrs.get("cf_turnstile_response")
        if not verify_turnstile(request, token):
            raise serializers.ValidationError({"cf_turnstile_response": "Invalid Turnstile token"})
        return attrs


# ==================== LOGIN SERIALIZERS ====================

class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    identifier = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=255,
        help_text="Username, phone number, or email"
    )
    password = serializers.CharField(
        write_only=True,
        allow_blank=False,
        min_length=8,
        max_length=128,
        help_text="User password"
    )
    remember_me = serializers.BooleanField(
        default=False,
        help_text="Extend token lifetime"
    )
    cf_turnstile_response = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        help_text="Cloudflare Turnstile token"
    )

    def validate_identifier(self, value):
        """Validate identifier format"""
        value = value.strip()
        
        # Phone number validation
        if value.startswith("+"):
            try:
                validate_user_mobile(value)
            except ValidationError as e:
                raise serializers.ValidationError(e.messages)
        # Email validation
        elif "@" in value:
            try:
                validate_user_email(value)
            except ValidationError as e:
                raise serializers.ValidationError(e.messages)
        # Username validation
        else:
            if len(value) < 3:
                raise serializers.ValidationError("Username is too short")
        
        return value

    def validate(self, attrs):
        """Validate login credentials"""
        identifier = attrs.get("identifier").strip()
        password = attrs.get("password")
        remember_me = attrs.get("remember_me", False)
        token = attrs.get("cf_turnstile_response", None)

        # Verify Turnstile token
        request = self.context.get("request")
        if not verify_turnstile(request, token):
            raise serializers.ValidationError({"cf_turnstile_response": "Invalid Turnstile token"})

        from ..services.auth_service import AuthService
        
        # Delegate to AuthService for secure authentication (handles lockout, failed counts, resets)
        user = AuthService.authenticate_user(identifier, password)
        
        if not user:
            # Check if reason is lockout to return accurate error, otherwise generic
            raw_user = AuthService.get_user_by_identifier(identifier)
            if raw_user and raw_user.is_locked():
                raise serializers.ValidationError("Account is locked due to too many failed attempts. Try again later.")
            raise serializers.ValidationError(
                "Username/Phone/Email/Password is incorrect"
            )

        attrs["user"] = user
        attrs["remember_me"] = remember_me
        return attrs


# ==================== TOKEN SERIALIZERS ====================

class RefreshTokenSerializer(serializers.Serializer):
    """Serializer for token refresh"""
    refresh = serializers.CharField(
        write_only=True,
        allow_blank=False,
        min_length=20,
        max_length=512,
        help_text="Valid refresh token"
    )


# ==================== 2FA SERIALIZERS ====================

class Enable2FASerializer(serializers.Serializer):
    """Serializer for enabling 2FA (no input fields required)"""
    
    def save(self, **kwargs):
        """Enable 2FA for the current user"""
        from ..services.twofa_service import TwoFAService
        
        user = self.context["request"].user
        result = TwoFAService.enable_2fa(user)
        return user


class TwoFACodeVerifySerializer(serializers.Serializer):
    """Serializer for verifying 2FA code"""
    session_id = serializers.UUIDField(
        help_text="2FA login session ID"
    )
    code = serializers.CharField(
        max_length=10,
        help_text="2FA verification code"
    )


class TwoFABackupVerifySerializer(serializers.Serializer):
    """Serializer for verifying 2FA backup code"""
    session_id = serializers.UUIDField(
        help_text="2FA login session ID"
    )
    backup_code = serializers.CharField(
        max_length=100,
        help_text="Backup code for 2FA"
    )


class SendOTPSerializer(serializers.Serializer):
    """POST /api/auth/otp/send/ — channel auto-detected from identifier format."""
    identifier = serializers.CharField(
        max_length=255,
        help_text="Email address or phone number. Channel (email/SMS) is auto-detected.",
    )
    cf_turnstile_response = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        help_text="Cloudflare Turnstile token"
    )

    def validate(self, attrs):
        request = self.context.get("request")
        token = attrs.get("cf_turnstile_response")
        if not verify_turnstile(request, token):
            raise serializers.ValidationError({"cf_turnstile_response": "Invalid Turnstile token"})
        return attrs


class VerifyOTPSerializer(serializers.Serializer):
    """POST /api/auth/otp/verify/"""
    identifier = serializers.CharField(max_length=255)
    otp = serializers.CharField(
        min_length=6,
        max_length=6,
        validators=[RegexValidator(r"^\d{6}$", "OTP must be exactly 6 digits")],
    )


class ForgotPasswordSerializer(serializers.Serializer):
    """POST /api/auth/password/forgot/"""
    identifier = serializers.CharField(
        max_length=255,
        help_text="Email address or phone number.",
    )
    cf_turnstile_response = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        help_text="Cloudflare Turnstile token"
    )

    def validate(self, attrs):
        request = self.context.get("request")
        token = attrs.get("cf_turnstile_response")
        if not verify_turnstile(request, token):
            raise serializers.ValidationError({"cf_turnstile_response": "Invalid Turnstile token"})
        return attrs


class ValidateResetTokenSerializer(serializers.Serializer):
    """GET /api/auth/password/validate-reset-token/?token=..."""
    token = serializers.CharField(min_length=64, max_length=64)


class ResetPasswordSerializer(serializers.Serializer):
    """POST /api/auth/password/reset/"""
    token = serializers.CharField(min_length=64, max_length=64)
    new_password = serializers.CharField(min_length=8, max_length=40, write_only=True)
    confirm_password = serializers.CharField(min_length=8, max_length=40, write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    """POST /api/auth/password/change/"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=8, max_length=40, write_only=True)
    confirm_password = serializers.CharField(min_length=8, max_length=40, write_only=True)
