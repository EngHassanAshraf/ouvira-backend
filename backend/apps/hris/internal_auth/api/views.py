"""
Internal Auth Views
===================
Thin view layer — delegates all logic to InternalAuthService.

Endpoints:
  POST /api/v1/hris/internal/auth/login/   → authenticate + return enriched JWT
  POST /api/v1/hris/internal/auth/logout/  → blacklist refresh token
  GET  /api/v1/hris/internal/auth/me/      → return current user context from token

Security:
  - Rate limited via ScopedRateThrottle ("internal_login" scope)
  - No Turnstile (internal network only)
  - IP extracted via django-ipware (respects X-Forwarded-For safely)
"""
import logging

from ipware import get_client_ip

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.shared.exceptions import BusinessException

from ..services.auth_service import InternalAuthService
from ..services.token_service import InternalTokenService
from .serializers import InternalLoginSerializer, InternalLogoutSerializer

logger = logging.getLogger(__name__)


def _get_ip(request) -> str:
    ip, _ = get_client_ip(request)
    return ip or "unknown"


def _get_ua(request) -> str:
    return request.META.get("HTTP_USER_AGENT", "")


class InternalLoginView(APIView):
    """
    POST /api/v1/hris/internal/auth/login/

    Authenticate an internal employee/staff user.

    Request body:
        {
            "identifier": "email@company.com",   // or username
            "password": "...",
            "company_id": 1                       // optional
        }

    Response (200):
        {
            "access_token": "...",
            "refresh_token": "...",
            "token_type": "Bearer",
            "expires_in": 900,
            "user": {
                "id": 1,
                "account_uid": "USR-...",
                "email": "...",
                "full_name": "...",
                "company_id": 1,
                "employee_id": "EMP-001",
                "roles": ["HR_ADMIN"],
                "permissions": ["hr.view_employee", "hr.edit_employee"],
                "modules": ["hr"]
            },
            "redirect": {
                "module": "hr",
                "path": "/hr/dashboard"
            }
        }
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "internal_login"

    def post(self, request):
        serializer = InternalLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": "Invalid input.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        identifier = serializer.validated_data["identifier"]
        password = serializer.validated_data["password"]
        company_id = serializer.validated_data.get("company_id")

        try:
            result = InternalAuthService.login(
                identifier=identifier,
                password=password,
                company_id=company_id,
                ip_address=_get_ip(request),
                user_agent=_get_ua(request),
            )
            return Response(result, status=status.HTTP_200_OK)

        except BusinessException as exc:
            # Return 401 for all auth failures — never 404 (prevents enumeration)
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception:
            logger.exception("InternalLoginView: unexpected error")
            return Response(
                {"detail": "An unexpected error occurred. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InternalLogoutView(APIView):
    """
    POST /api/v1/hris/internal/auth/logout/

    Blacklist the provided refresh token.

    Request body:
        { "refresh_token": "..." }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InternalLogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": "refresh_token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh_token = serializer.validated_data["refresh_token"]
        success = InternalTokenService.blacklist(refresh_token)

        if success:
            return Response(
                {"detail": "Logged out successfully."},
                status=status.HTTP_205_RESET_CONTENT,
            )
        return Response(
            {"detail": "Invalid or already expired token."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class InternalMeView(APIView):
    """
    GET /api/v1/hris/internal/auth/me/

    Returns the current authenticated user's context decoded from the JWT.
    No DB query — reads claims directly from the validated token.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = request.auth  # SimpleJWT AccessToken instance

        # Extract enriched claims added by InternalTokenService
        return Response(
            {
                "user_id": token.get("user_id"),
                "company_id": token.get("company_id"),
                "employee_id": token.get("employee_id"),
                "roles": token.get("roles", []),
                "permissions": token.get("permissions", []),
                "modules": token.get("modules", []),
                "token_type": token.get("token_type"),
            },
            status=status.HTTP_200_OK,
        )
