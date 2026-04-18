"""
Ouvira ERP — Root URL Configuration
=====================================
Structure:
  /                        → API root info
  /health/                 → Health check
  /admin/                  → Django admin
  /api/v1/auth/            → Authentication & 2FA (identity.auth_app)
  /api/v1/account/         → User profile & management (identity.account)
  /api/v1/access-control/  → Roles, permissions, invitations
  /api/v1/company/         → Company management
  /api/v1/hris/            → HRIS modules (core, recruitment, ...)
  /api/v1/audit/           → Activity logs, notifications, security audit
  /swagger/                → Swagger UI
  /redoc/                  → ReDoc UI
  /swagger.json|yaml       → OpenAPI schema
"""

import datetime

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny

# ---------------------------------------------------------------------------
# OpenAPI / Swagger schema
# ---------------------------------------------------------------------------

schema_view = get_schema_view(
    openapi.Info(
        title="Ouvira ERP API",
        default_version="v1",
        description=(
            "Production-grade REST API for the Ouvira ERP platform.\n\n"
            "All endpoints are versioned under `/api/v1/`. "
            "Authenticate via `Authorization: Bearer <access_token>`."
        ),
        contact=openapi.Contact(email="support@ouvira.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=(AllowAny,),
)

# ---------------------------------------------------------------------------
# Utility views
# ---------------------------------------------------------------------------

def api_root(request):
    """Minimal root endpoint — useful for load-balancer probes and discovery."""
    return JsonResponse(
        {
            "service": "Ouvira ERP API",
            "version": "v1",
            "docs": "/swagger/",
            "health": "/health/",
        }
    )


def health_check(request):
    """Liveness probe — returns 200 as long as the process is alive."""
    return JsonResponse(
        {
            "status": "ok",
            "service": "ouvira-backend",
            "version": "v1",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        }
    )

# ---------------------------------------------------------------------------
# API v1 URL groups
# ---------------------------------------------------------------------------

# Each tuple: (prefix, app_module, namespace)
_V1_ROUTES = [
    # Identity
    ("auth/",           "apps.identity.auth_app.api.urls",  "auth"),
    ("account/",        "apps.identity.account.api.urls",   "account"),
    # Access control
    ("access-control/", "apps.access_control.api.urls",     "access-control"),
    # Company
    ("company/",        "apps.company.api.urls",            "company"),
    # HRIS (aggregated via hris/base/urls.py)
    ("hris/",           "apps.hris.base.urls",              "hris"),
    # Audit
    ("audit/",          "apps.audit.api.urls",              "audit"),
]

v1_urlpatterns = [
    path(prefix, include((module, namespace)))
    for prefix, module, namespace in _V1_ROUTES
]

# ---------------------------------------------------------------------------
# Root urlpatterns
# ---------------------------------------------------------------------------

urlpatterns = [
    # --- Utility ---
    path("", api_root, name="api-root"),
    path("health/", health_check, name="health-check"),

    # --- Admin ---
    path("admin/", admin.site.urls),

    # --- API v1 ---
    path("api/v1/", include((v1_urlpatterns, "v1"))),

    # --- OpenAPI schema (machine-readable) ---
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),

    # --- API documentation UIs ---
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
