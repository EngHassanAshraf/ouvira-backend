from django.urls import path

from .views import (
    PermissionListCreateView,
    PermissionDetailView,
    RoleListCreateView,
    RoleDetailView,
    RolePermissionListCreateView,
    RolePermissionDetailView,
    UserCompanyListCreateView,
    UserCompanyDetailView,
    UserCompanyRoleListCreateView,
    UserCompanyRoleDetailView,
    InvitationListCreateView,
    InvitationDetailView,
    InvitationAcceptView,
    InvitationRevokeView,
    InvitationResendView,
)

app_name = "access-control"

urlpatterns = [
    # --- Permissions ---
    path("permissions/", PermissionListCreateView.as_view(), name="permission-list"),
    path("permissions/<int:pk>/", PermissionDetailView.as_view(), name="permission-detail"),

    # --- Roles ---
    path("roles/", RoleListCreateView.as_view(), name="role-list"),
    path("roles/<int:pk>/", RoleDetailView.as_view(), name="role-detail"),

    # --- Role ↔ Permission assignments ---
    path("role-permissions/", RolePermissionListCreateView.as_view(), name="role-permission-list"),
    path("role-permissions/<int:pk>/", RolePermissionDetailView.as_view(), name="role-permission-detail"),

    # --- User ↔ Company memberships ---
    path("user-companies/", UserCompanyListCreateView.as_view(), name="user-company-list"),
    path("user-companies/<int:pk>/", UserCompanyDetailView.as_view(), name="user-company-detail"),

    # --- User ↔ Company ↔ Role assignments ---
    path("user-company-roles/", UserCompanyRoleListCreateView.as_view(), name="user-company-role-list"),
    path("user-company-roles/<int:pk>/", UserCompanyRoleDetailView.as_view(), name="user-company-role-detail"),

    # --- Invitations ---
    path("invitations/", InvitationListCreateView.as_view(), name="invitation-list"),
    path("invitations/accept/", InvitationAcceptView.as_view(), name="invitation-accept"),
    path("invitations/<int:pk>/", InvitationDetailView.as_view(), name="invitation-detail"),
    path("invitations/<int:pk>/revoke/", InvitationRevokeView.as_view(), name="invitation-revoke"),
    path("invitations/<int:pk>/resend/", InvitationResendView.as_view(), name="invitation-resend"),
]
