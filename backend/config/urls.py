from django.contrib import admin
from django.urls import path, include, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok"})

schema_view = get_schema_view(
    openapi.Info(
        title="Ouvira API",
        default_version="v1",
        description="Ouvira API documentation",
    ),
    public=True,
    permission_classes=(AllowAny,),
)

urlpatterns = [
    path("", health_check),
    path("api/access-control/", include("apps.access_control.api.urls")),
    path("api/auth/", include("apps.identity.auth_app.api.urls")),
    path("api/account/", include("apps.identity.account.api.urls")),
    path("api/company/", include("apps.company.api.urls")),
    path("api/audit/", include("apps.audit.api.urls")),
    path("admin/", admin.site.urls),
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
