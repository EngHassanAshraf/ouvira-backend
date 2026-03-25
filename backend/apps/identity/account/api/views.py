"""
Account views — user profile management and admin user listing.
"""
import datetime
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from ..services import AccountService
from .serializers import UserProfileSerializer, UserUpdateSerializer, UserListSerializer
from apps.access_control.permissions.IsAdminUser import IsAdminUser


class UserProfileView(RetrieveUpdateAPIView):
    """
    GET   /profile/ → retrieve authenticated user's profile
    PUT   /profile/ → update profile
    PATCH /profile/ → partial update
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserProfileSerializer

    def get_object(self):
        return AccountService.get_profile(self.request.user)

    def perform_update(self, serializer):
        AccountService.update_profile(self.request.user, **serializer.validated_data)


class UserListView(ListAPIView):
    """
    GET /users/ → list users (admin only)
    Supports ?company=<id> query param to filter by company.
    """
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        company_id = self.request.query_params.get("company")
        if company_id is not None:
            try:
                company_id = int(company_id)
            except (ValueError, TypeError):
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"error": "invalid company_id — must be an integer"})
        return AccountService.list_users(company_id=company_id)


class SessionTestAPIView(APIView):
    """Session/token inspection endpoint for debugging."""
    permission_classes = [IsAuthenticated, IsAdminUser]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        token = request.auth

        if hasattr(token, "payload"):
            exp_timestamp = token.payload.get("exp")
        else:
            exp_timestamp = None

        if exp_timestamp:
            exp_datetime = datetime.datetime.fromtimestamp(exp_timestamp)
        else:
            exp_datetime = None

        return Response(
            {
                "user": str(user),
                "token_expires_at": exp_datetime,
            }
        )
