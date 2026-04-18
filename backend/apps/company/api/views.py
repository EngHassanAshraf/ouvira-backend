"""
Company views — full CRUD with service layer integration.
"""
import logging
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT

from ..models import CompanySettings
from ..services import CompanyService, CompanySettingsService
from ..permissions import IsCompanyOwner, IsCompanyAdmin
from .serializers import (
    CompanyListSerializer,
    CompanyDetailSerializer,
    CompanySettingsSerializer,
)

logger = logging.getLogger(__name__)


class CompanyListCreateView(ListCreateAPIView):
    """
    GET  / → list companies accessible to the authenticated user
    POST / → create a new company
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CompanyListSerializer
        return CompanyDetailSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            from ..models import Company
            return Company.objects.none()
        return CompanyService.get_companies_for_user(self.request.user)

    def perform_create(self, serializer):
        company = serializer.save()
        company = serializer.save()
        # Auto-create default settings for new company
        CompanySettingsService.get_or_create_settings(company)


class CompanyDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET    /<pk>/ → retrieve company detail (authenticated member)
    PUT    /<pk>/ → update company (admin or owner)
    PATCH  /<pk>/ → partial update (admin or owner)
    DELETE /<pk>/ → soft delete company (owner only)
    """
    serializer_class = CompanyDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsCompanyOwner()]
        if self.request.method in ("PUT", "PATCH"):
            return [IsAuthenticated(), IsCompanyAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            from ..models import Company
            return Company.objects.none()
        return CompanyService.get_companies_for_user(self.request.user)

    def perform_destroy(self, instance):
        CompanyService.soft_delete_company(instance)


class CompanySettingsView(RetrieveUpdateAPIView):
    """
    GET   /<pk>/settings/ → retrieve settings for a company
    PUT   /<pk>/settings/ → update settings (admin or owner)
    PATCH /<pk>/settings/ → partial update settings (admin or owner)
    """
    serializer_class = CompanySettingsSerializer
    permission_classes = [IsAuthenticated]
    queryset = CompanySettings.objects.all()  # satisfies drf-yasg; get_object overrides

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH"):
            return [IsAuthenticated(), IsCompanyAdmin()]
        return super().get_permissions()

    def get_object(self):
        if getattr(self, "swagger_fake_view", False):
            return CompanySettings()
        company_pk = self.kwargs["pk"]
        # Verify user has access to this company
        company = CompanyService.get_company(company_pk, user=self.request.user)
        # Get or create settings
        return CompanySettingsService.get_or_create_settings(company)
