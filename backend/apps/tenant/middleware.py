from django.conf import settings
from django_tenants.middleware.main import TenantMainMiddleware

class HeaderTenantMainMiddleware(TenantMainMiddleware):
    TENANT_HEADER = "HTTP_X_TENANT"

def process_request(self, request):
    header_value = request.META.get(self.TENANT_HEADER)
    print(f"DEBUG x-tenant header: {header_value}")
    print(f"DEBUG HTTP_HOST before: {request.META.get('HTTP_HOST')}")
    if header_value:
        tenant_host = header_value.strip()
        base_domain = getattr(settings, "TENANT_BASE_DOMAIN", "")
        if "." not in tenant_host and base_domain:
            tenant_host = f"{tenant_host}.{base_domain}"
        request.META["HTTP_HOST"] = tenant_host
    print(f"DEBUG HTTP_HOST after: {request.META.get('HTTP_HOST')}")
    return super().process_request(request)