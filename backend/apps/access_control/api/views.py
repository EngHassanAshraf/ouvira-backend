"""
Access control views using service layer with combined generic views.
Each URL path maps to exactly one view that dispatches by HTTP method.
"""
import logging
from django.db.models.query import QuerySet
from rest_framework.views import APIView
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from .serializers import (
    PermissionSerializer,
    PermissionListSerializer,
    RoleSerializer,
    RoleListSerializer,
    RolePermissionSerializer,
    UserCompanySerializer,
    UserCompanyRoleSerializer,
    InvitationSerializer,
    InvitationListSerializer,
)

from ..services import (
    PermissionService,
    RoleService,
    RolePermissionService,
    UserCompanyService,
    UserCompanyRoleService,
    InvitationService,
)
from ..permissions.IsAdminUser import IsAdminUser
from apps.shared.exceptions import BusinessException

logger = logging.getLogger(__name__)


# ==================== PERMISSION VIEWS ====================

class PermissionListCreateView(ListCreateAPIView):
    """
    GET  /permissions/ → list all permissions (any authenticated user)
    POST /permissions/ → create a new permission (admin only)
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PermissionListSerializer
        return PermissionSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self) -> QuerySet:
        return PermissionService.get_active_permissions()


class PermissionDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET    /permissions/<pk>/ → retrieve (any authenticated user)
    PUT    /permissions/<pk>/ → update (admin only)
    PATCH  /permissions/<pk>/ → partial update (admin only)
    DELETE /permissions/<pk>/ → soft delete (admin only)
    """

    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        return PermissionService.get_active_permissions()

    def perform_destroy(self, instance):
        PermissionService.soft_delete_permission(instance)


# ==================== ROLE VIEWS ====================

class RoleListCreateView(ListCreateAPIView):
    """
    GET  /roles/ → list roles for user's companies
    POST /roles/ → create a new role (admin only)
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return RoleListSerializer
        return RoleSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self) -> QuerySet:
        if getattr(self, "swagger_fake_view", False):
            from ..models import Role
            return Role.objects.none()
        company_id = self.request.query_params.get("company")
        return RoleService.get_roles_for_user(
            self.request.user,
            company_id=int(company_id) if company_id else None,
        )

    def create(self, request, *args, **kwargs):
        company_id = request.data.get("company")
        if not company_id:
            return Response(
                {"detail": "Company is required."},
                status=HTTP_400_BAD_REQUEST,
            )

        try:
            RoleService.verify_company(company_id)
        except Exception:
            return Response(
                {"detail": "Company not found."},
                status=HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)


class RoleDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET    /roles/<pk>/ → retrieve
    PUT    /roles/<pk>/ → update (admin only)
    PATCH  /roles/<pk>/ → partial update (admin only)
    DELETE /roles/<pk>/ → soft delete (admin only)
    """

    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            from ..models import Role
            return Role.objects.none()
        return RoleService.get_roles_for_user(self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        company_id = request.query_params.get("company")
        if not company_id:
            return Response(
                {"detail": "Company is required as query parameter."},
                status=HTTP_400_BAD_REQUEST,
            )

        try:
            RoleService.soft_delete_role(instance, company_id=int(company_id))
            return Response(status=HTTP_204_NO_CONTENT)
        except BusinessException as e:
            return Response(
                {"detail": str(e)},
                status=HTTP_403_FORBIDDEN,
            )
        except ValueError:
            return Response(
                {"detail": "Invalid company ID."},
                status=HTTP_400_BAD_REQUEST,
            )


# ==================== ROLE PERMISSION VIEWS ====================

class RolePermissionListCreateView(ListCreateAPIView):
    """
    GET  /role-permissions/ → list role permissions
    POST /role-permissions/ → assign permission to role (admin only)
    """

    serializer_class = RolePermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self) -> QuerySet:
        if getattr(self, "swagger_fake_view", False):
            from ..models import RolePermission
            return RolePermission.objects.none()
        role_id = self.request.query_params.get("role")
        return RolePermissionService.get_role_permissions_for_user(
            self.request.user,
            role_id=int(role_id) if role_id else None,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role = serializer.validated_data.get("role")
        if role and role.company:
            company_id = role.company.id
            if not request.data.get("company") and not request.query_params.get(
                "company"
            ):
                request.data["company"] = company_id

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)


class RolePermissionDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET    /role-permissions/<pk>/ → retrieve
    PUT    /role-permissions/<pk>/ → update (admin only)
    PATCH  /role-permissions/<pk>/ → partial update (admin only)
    DELETE /role-permissions/<pk>/ → remove permission from role (admin only)
    """

    serializer_class = RolePermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            from ..models import RolePermission
            return RolePermission.objects.none()
        return RolePermissionService.get_role_permissions_for_user(self.request.user)

    def perform_destroy(self, instance):
        RolePermissionService.remove_permission_from_role(instance)


# ==================== USER COMPANY VIEWS ====================

class UserCompanyListCreateView(ListCreateAPIView):
    """
    GET  /user-companies/ → list user-company associations
    POST /user-companies/ → associate user with company (admin only)
    """

    serializer_class = UserCompanySerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self) -> QuerySet:
        if getattr(self, "swagger_fake_view", False):
            from ..models import UserCompany
            return UserCompany.objects.none()
        user_id = self.request.query_params.get("user")
        company_id = self.request.query_params.get("company")

        is_admin = UserCompanyService.is_user_admin(self.request.user)

        queryset = UserCompanyService.get_user_companies(
            self.request.user,
            filter_by_user=not is_admin,
        )

        if is_admin:
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            if company_id:
                queryset = queryset.filter(company_id=company_id)

        return queryset

    def create(self, request, *args, **kwargs):
        company_id = request.data.get("company")
        if not company_id:
            return Response(
                {"detail": "Company is required."},
                status=HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)


class UserCompanyDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET    /user-companies/<pk>/ → retrieve
    PUT    /user-companies/<pk>/ → update (admin only)
    PATCH  /user-companies/<pk>/ → partial update (admin only)
    DELETE /user-companies/<pk>/ → remove user from company (admin only)
    """

    serializer_class = UserCompanySerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            from ..models import UserCompany
            return UserCompany.objects.none()
        return UserCompanyService.get_user_companies(
            self.request.user,
            filter_by_user=not UserCompanyService.is_user_admin(self.request.user),
        )

    def perform_destroy(self, instance):
        UserCompanyService.remove_user_from_company(instance)


# ==================== USER COMPANY ROLE VIEWS ====================

class UserCompanyRoleListCreateView(ListCreateAPIView):
    """
    GET  /user-company-roles/ → list user-company-role assignments
    POST /user-company-roles/ → assign role to user-company (admin only)
    """

    serializer_class = UserCompanyRoleSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self) -> QuerySet:
        if getattr(self, "swagger_fake_view", False):
            from ..models import UserCompanyRole
            return UserCompanyRole.objects.none()
        user_company_id = self.request.query_params.get("user_company")
        role_id = self.request.query_params.get("role")

        return UserCompanyRoleService.get_user_company_roles_for_user(
            self.request.user,
            user_company_id=int(user_company_id) if user_company_id else None,
            role_id=int(role_id) if role_id else None,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_company = serializer.validated_data.get("user_company")
        if user_company and user_company.company:
            company_id = user_company.company.id
            if not request.data.get("company") and not request.query_params.get(
                "company"
            ):
                request.data["company"] = company_id

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)


class UserCompanyRoleDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET    /user-company-roles/<pk>/ → retrieve
    PUT    /user-company-roles/<pk>/ → update (admin only)
    PATCH  /user-company-roles/<pk>/ → partial update (admin only)
    DELETE /user-company-roles/<pk>/ → remove role (admin only)
    """

    serializer_class = UserCompanyRoleSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            from ..models import UserCompanyRole
            return UserCompanyRole.objects.none()
        return UserCompanyRoleService.get_user_company_roles_for_user(self.request.user)

    def perform_destroy(self, instance):
        UserCompanyRoleService.remove_role_from_user(instance)


# ==================== INVITATION VIEWS ====================

class InvitationListCreateView(ListCreateAPIView):
    """
    GET  /invitations/ → list invitations
    POST /invitations/ → create invitation (admin only)
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return InvitationListSerializer
        return InvitationSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self) -> QuerySet:
        if getattr(self, "swagger_fake_view", False):
            from ..models import Invitation
            return Invitation.objects.none()
        company_id = self.request.query_params.get("company")
        status_filter = self.request.query_params.get("status")

        return InvitationService.get_invitations_for_user(
            self.request.user,
            company_id=int(company_id) if company_id else None,
            status=status_filter,
        )

    def create(self, request, *args, **kwargs):
        company_id = request.data.get("company")
        if not company_id:
            return Response(
                {"detail": "Company is required."},
                status=HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            invitation = InvitationService.create_invitation(
                company=serializer.validated_data["company"],
                email=serializer.validated_data["email"],
                role=serializer.validated_data["role"],
                invited_by=request.user,
                expires_at=serializer.validated_data.get("expires_at"),
                token=serializer.validated_data.get("token"),
            )

            return Response(
                InvitationSerializer(invitation).data,
                status=HTTP_201_CREATED,
            )
        except BusinessException as e:
            return Response(
                {"detail": str(e)},
                status=HTTP_400_BAD_REQUEST,
            )


class InvitationDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET    /invitations/<pk>/ → retrieve
    PUT    /invitations/<pk>/ → update (admin only)
    PATCH  /invitations/<pk>/ → partial update (admin only)
    DELETE /invitations/<pk>/ → delete (admin only)
    """

    serializer_class = InvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            from ..models import Invitation
            return Invitation.objects.none()
        return InvitationService.get_invitations_for_user(self.request.user)


class InvitationAcceptView(APIView):
    """Accept an invitation by token"""

    permission_classes = []

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response(
                {"detail": "Token is required."},
                status=HTTP_400_BAD_REQUEST,
            )

        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required to accept invitation."},
                status=HTTP_403_FORBIDDEN,
            )

        try:
            user_company, user_company_role = InvitationService.accept_invitation(
                token=token,
                user=request.user,
            )

            return Response(
                {
                    "detail": "Invitation accepted successfully.",
                    "user_company": UserCompanySerializer(user_company).data,
                    "role": RoleSerializer(user_company_role.role).data,
                },
                status=HTTP_200_OK,
            )
        except BusinessException as e:
            return Response(
                {"detail": str(e)},
                status=HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.exception("Error accepting invitation")
            return Response(
                {"detail": "Invalid or expired invitation token."},
                status=HTTP_404_NOT_FOUND,
            )


class InvitationRevokeView(APIView):
    """Revoke an invitation (Admin only)"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
        try:
            invitation = InvitationService.get_invitation(pk, user=request.user)
        except Exception:
            return Response(
                {"detail": "Invitation not found."},
                status=HTTP_404_NOT_FOUND,
            )

        company_id = request.data.get("company") or request.query_params.get("company")
        if not company_id:
            return Response(
                {"detail": "Company is required."},
                status=HTTP_400_BAD_REQUEST,
            )

        if invitation.company.id != int(company_id):
            return Response(
                {"detail": "You don't have permission to revoke this invitation."},
                status=HTTP_403_FORBIDDEN,
            )

        try:
            InvitationService.revoke_invitation(invitation)
            return Response(
                {"detail": "Invitation revoked successfully."},
                status=HTTP_200_OK,
            )
        except BusinessException as e:
            return Response(
                {"detail": str(e)},
                status=HTTP_400_BAD_REQUEST,
            )


class InvitationResendView(APIView):
    """Resend an invitation (Admin only)"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
        try:
            invitation = InvitationService.get_invitation(pk, user=request.user)
        except Exception:
            return Response(
                {"detail": "Invitation not found."},
                status=HTTP_404_NOT_FOUND,
            )

        company_id = request.data.get("company") or request.query_params.get("company")
        if not company_id or invitation.company.id != int(company_id):
            return Response(
                {"detail": "You don't have permission to resend this invitation."},
                status=HTTP_403_FORBIDDEN,
            )

        try:
            invitation = InvitationService.resend_invitation(invitation)
            return Response(
                {
                    "detail": "Invitation resent successfully.",
                    "invitation": InvitationSerializer(invitation).data,
                },
                status=HTTP_200_OK,
            )
        except BusinessException as e:
            return Response(
                {"detail": str(e)},
                status=HTTP_400_BAD_REQUEST,
            )
