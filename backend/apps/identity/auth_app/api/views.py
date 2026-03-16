"""
Optimized authentication views using service layer
"""
import logging

from django.conf import settings
from django.db import IntegrityError, DatabaseError

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from drf_yasg.utils import swagger_auto_schema

from .serializers import (
    Enable2FASerializer,
    SignupSerializer,
    RefreshTokenSerializer,
    OTPVerifySerializer,
    ResentOTPSerializer,
    LoginSerializer,
    TwoFACodeVerifySerializer,
    TwoFABackupVerifySerializer,
    FinalizeSignInSerializer,
)

from ..services import (
    AuthService,
    OTPService,
    TwoFAService,
    TokenService,
    LoginActivityService,
)

from apps.identity.account.services import UserService
from apps.shared.exceptions import BusinessException
from apps.shared.messages.error import ERROR_MESSAGES
from apps.shared.messages.success import SUCCESS_MESSAGES
from apps.shared.services.sms_service import send_sms

logger = logging.getLogger(__name__)


# ==================== SIGNUP VIEWS ====================

class SignUPView(APIView):
    """User signup endpoint"""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "signup"

    @swagger_auto_schema(request_body=SignupSerializer)
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data.get("primary_mobile")
        full_name = serializer.validated_data.get("full_name")


        try:
            # Create or get user
            user, created = AuthService.signup_user(phone_number, full_name)
            
            # Generate and send OTP
            otp = OTPService.create_otp(phone_number)
            
            # Send SMS
            send_sms(message=f"Your OTP code is {otp.otp_code}", phone=phone_number)
            return Response(
                {
                    "status": "success",
                    "message": SUCCESS_MESSAGES["PHONE_OTP_SENT"]
                },
                status=status.HTTP_200_OK,
            )

        except IntegrityError:
            logger.error(f"Integrity error during signup for {phone_number}")
            return Response(
                {
                    "status": "error",
                    "message": ERROR_MESSAGES["MOBILE_ALREADY_USED"]
                },
                status=status.HTTP_409_CONFLICT,
            )
        except DatabaseError as e:
            logger.exception(f"Database error during signup for {phone_number}")
            return Response(
                {
                    "status": "error",
                    "message": ERROR_MESSAGES["SYSTEM_ERROR"]
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.exception(f"Unexpected error during signup for {phone_number}")
            return Response(
                {
                    "status": "error",
                    "message": ERROR_MESSAGES["SYSTEM_ERROR"]
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ==================== OTP VIEWS ====================

class OTPVerifyView(APIView):
    """OTP verification endpoint"""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_verify"

    @swagger_auto_schema(request_body=OTPVerifySerializer)
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data.get("primary_mobile")
        otp_code = serializer.validated_data.get("otp_code")

        try:
            # Verify OTP
            is_valid, error_message = OTPService.verify_otp(phone_number, otp_code)
            
            if not is_valid:
                return Response(
                    {
                        "status": "error",
                        "message": error_message
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verify phone number
            user = AuthService.verify_phone_number(phone_number)
            
            # Delete OTP after successful verification
            OTPService.delete_otp(phone_number)

            return Response(
                {
                    "status": "success",
                    "message": SUCCESS_MESSAGES["MOBILE_VALIDATED"]
                },
                status=status.HTTP_200_OK,
            )

        except BusinessException as e:
            logger.warning(f"Business error during OTP verification: {e.message}")
            return Response(
                {
                    "status": "error",
                    "message": e.message
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except DatabaseError as e:
            logger.exception("Database error during OTP verification")
            return Response(
                {
                    "status": "error",
                    "message": ERROR_MESSAGES["SYSTEM_ERROR"]
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.exception("Unexpected error during OTP verification")
            return Response(
                {
                    "status": "error",
                    "message": ERROR_MESSAGES["SYSTEM_ERROR"]
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ResentOTPView(APIView):
    """Resend OTP endpoint"""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_resend"

    @swagger_auto_schema(request_body=ResentOTPSerializer, security=[])
    def post(self, request):
        from ..utils import verify_turnstile
        
        # Verify Turnstile token
        token = request.data.get("cf-turnstile-response")
        if not token or not verify_turnstile(token, request.META.get("REMOTE_ADDR")):
            return Response(
                {
                    "status": "error",
                    "message": ERROR_MESSAGES["SYSTEM_ERROR"]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ResentOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["primary_mobile"]

        # Check if user exists
        from apps.identity.account.models.user import CustomUser
        if not CustomUser.objects.filter(primary_mobile=phone_number).exists():
            return Response(
                {
                    "status": "error",
                    "message": ERROR_MESSAGES["ACCOUNT_NOT_FOUND"]
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Generate new OTP
        OTPService.create_otp(phone_number)

        return Response(
            {
                "status": "success",
                "message": SUCCESS_MESSAGES["PHONE_OTP_SENT"],
                "expiry": "60 minutes",
            },
            status=status.HTTP_200_OK,
        )


# ==================== FINALIZE SIGNUP VIEW ====================

class FinalizeSignInView(APIView):
    """Finalize signup with email and password"""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "finalize_signin"

    @swagger_auto_schema(request_body=FinalizeSignInSerializer)
    def post(self, request):
        serializer = FinalizeSignInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        primary_mobile = serializer.validated_data.get("primary_mobile")
        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")

        try:
            # Get user
            from apps.identity.account.models.user import CustomUser
            user = CustomUser.objects.filter(primary_mobile=primary_mobile).first()
            
            if not user:
                return Response(
                    {
                        "status": "error",
                        "message": ERROR_MESSAGES["ACCOUNT_NOT_FOUND"]
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Finalize signup
            AuthService.finalize_signup(user, email, password)
            
            # Update user via UserService
            user = UserService.update_existing_user(**serializer.validated_data)

            logger.info(f"User {primary_mobile} successfully finalized signup")
            
            return Response(
                {
                    "status": "success",
                    "message": SUCCESS_MESSAGES["ASSIGNED_AS_OWNER"]
                },
                status=status.HTTP_200_OK,
            )

        except BusinessException as e:
            logger.warning(f"Business error during finalizing sign-in: {e.message}")
            return Response(
                {
                    "status": "error",
                    "message": e.message
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValueError as e:
            logger.warning(f"Validation error during finalizing sign-in: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.exception("Unexpected error during finalizing sign-in")
            return Response(
                {
                    "status": "error",
                    "message": ERROR_MESSAGES["SYSTEM_ERROR"]
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ==================== LOGIN VIEWS ====================

class LoginView(APIView):
    """User login endpoint"""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            # Handle failed login attempts
            identifier = request.data.get("identifier")
            if identifier:
                user = AuthService.get_user_by_identifier(identifier)
                if user:
                    user.failed_login_attempts += 1
                    if user.failed_login_attempts >= 5:
                        user.lock_account(minutes=30)
                    else:
                        user.save(update_fields=["failed_login_attempts"])

            return Response(
                {
                    "message": ERROR_MESSAGES["LOGIN_CREDENTIALS_INCORRECT"]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data["user"]
        remember_me = serializer.validated_data["remember_me"]

        # Check if 2FA is enabled
        if user.is_2fa_enabled:
            # Create 2FA session
            session = TwoFAService.create_login_session(user)
            
            # Generate 2FA code (for dev/testing)
            generated_code = TwoFAService.generate_2fa_code(user)
            
            # Record login activity
            LoginActivityService.record_login(user, request)

            return Response(
                {
                    "message": SUCCESS_MESSAGES.get(
                        "VERIFICATION_ACCEPTED", "2FA verification required"
                    ),
                    "2fa_required": True,
                    "session_id": str(session.session_id),
                    "generated_code": generated_code,  # Remove in production
                },
                status=status.HTTP_200_OK,
            )

        # Regular login without 2FA
        tokens = TokenService.generate_tokens(user, remember_me)
        
        # Record login activity
        LoginActivityService.record_login(user, request)

        return Response(
            {
                "message": SUCCESS_MESSAGES["LOGIN_SUCCESS"],
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "expires_in": tokens["expires_in"],
                "2fa_required": False,
            },
            status=status.HTTP_200_OK,
        )


# ==================== TOKEN VIEWS ====================

class RefreshTokenView(APIView):
    """Refresh access token endpoint"""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "refresh"

    @swagger_auto_schema(request_body=RefreshTokenSerializer)
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]
        
        try:
            tokens = TokenService.refresh_access_token(refresh_token)
            return Response(tokens, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return Response(
                {
                    "message": ERROR_MESSAGES["SYSTEM_ERROR"]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class LogoutView(APIView):
    """User logout endpoint"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {
                        "message": ERROR_MESSAGES["SYSTEM_ERROR"]
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            success = TokenService.blacklist_token(refresh_token)
            
            if success:
                return Response(
                    {
                        "message": SUCCESS_MESSAGES["LOGGED_OUT"]
                    },
                    status=status.HTTP_205_RESET_CONTENT,
                )
            else:
                return Response(
                    {
                        "message": ERROR_MESSAGES["SYSTEM_ERROR"]
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response(
                {
                    "message": ERROR_MESSAGES["SYSTEM_ERROR"]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


# ==================== 2FA VIEWS ====================

class Enable2FAView(APIView):
    """Enable 2FA endpoint"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "enable_2fa"

    @swagger_auto_schema(request_body=Enable2FASerializer)
    def post(self, request):
        serializer = Enable2FASerializer(
            data={},
            context={"request": request}
        )
        
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response(
                {
                    "message": SUCCESS_MESSAGES["VERIFICATION_ACCEPTED"],
                    "backup_codes": serializer.instance.backup_codes,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Enable 2FA error: {str(e)}")
            return Response(
                {
                    "message": ERROR_MESSAGES["SYSTEM_ERROR"]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class TwoFAVerifyCodeView(APIView):
    """Verify 2FA code endpoint"""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "twofa_verify"

    @swagger_auto_schema(request_body=TwoFACodeVerifySerializer, security=[])
    def post(self, request):
        serializer = TwoFACodeVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data["session_id"]
        code = serializer.validated_data["code"]

        # Verify 2FA session
        user, error_message = TwoFAService.verify_2fa_session(session_id, code)
        
        if not user:
            return Response(
                {
                    "error": error_message
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate tokens
        tokens = TokenService.generate_tokens(user)
        
        # Record login activity
        LoginActivityService.record_login(user, request)

        return Response(
            {
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "expires_in": tokens["expires_in"],
                "message": "Login successful",
            },
            status=status.HTTP_200_OK,
        )


class TwoFAVerifyBackupView(APIView):
    """Verify 2FA backup code endpoint"""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "twofa_verify"

    @swagger_auto_schema(request_body=TwoFABackupVerifySerializer)
    def post(self, request):
        serializer = TwoFABackupVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data["session_id"]
        backup_code = serializer.validated_data["backup_code"]

        # Verify 2FA backup session
        user, error_message = TwoFAService.verify_2fa_backup_session(session_id, backup_code)
        
        if not user:
            return Response(
                {
                    "message": error_message
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate tokens
        tokens = TokenService.generate_tokens(user)
        
        # Record login activity
        LoginActivityService.record_login(user, request)

        return Response(
            {
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "expires_in": tokens["expires_in"],
                "message": SUCCESS_MESSAGES["VERIFICATION_ACCEPTED"],
            },
            status=status.HTTP_200_OK,
        )
