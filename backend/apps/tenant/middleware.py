from django.conf import settings
from django.db import connection
from django_tenants.middleware.main import TenantMainMiddleware
from django_tenants.utils import get_public_schema_name


class HeaderTenantMainMiddleware(TenantMainMiddleware):
    TENANT_HEADER = "HTTP_X_TENANT"

    # Paths that should always resolve to the public schema (no tenant required)
    PUBLIC_SCHEMA_PATHS = ("/health/", "/", "/admin/", "/swagger/", "/redoc/")

    def process_request(self, request):
        # Fall back to public schema for health checks and admin paths
        if request.path_info in self.PUBLIC_SCHEMA_PATHS or request.path_info.startswith("/swagger"):
            connection.set_schema_to_public()
            return None

        header_value = request.META.get(self.TENANT_HEADER)
        if header_value:
            tenant_host = header_value.strip()
            base_domain = getattr(settings, "TENANT_BASE_DOMAIN", "")
            if "." not in tenant_host and base_domain:
                tenant_host = f"{tenant_host}.{base_domain}"
            request.META["HTTP_HOST"] = tenant_host
        return super().process_request(request)