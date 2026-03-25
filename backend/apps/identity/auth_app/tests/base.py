import os
from django.test import override_settings, TestCase
from rest_framework.test import APIClient

# --- [SETUP] Fixes for the Test Environment ---
# 1. Redis not available: Override CACHES to use LocMemCache
#    so rate limits work in memory without needing actual Redis.
caches_override = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient

class BaseAuthTestCase(TenantTestCase):
    """
    Base test class for auth_app.
    Applies the required [SETUP] fixes so that:
    - Redis caches use local memory
    - Rate limits use the local memory cache
    - Celery tasks run synchronously and propagate exceptions
    - Tenant schema routing is set up for multi-tenant APIs (prevents 404s)
    """
    
    @classmethod
    def setup_tenant(cls, tenant):
        """Add any extra tenant data needed here."""
        tenant.name = "Test Tenant"
        tenant.paid_until = "2099-12-31"
        tenant.on_trial = False

    def setUp(self):
        super().setUp()
        # Create an APIClient initialized with the tenant's domain
        # so the django-tenant middleware doesn't crash on get_host()
        domain = self.tenant.get_primary_domain().domain
        self.client = APIClient(
            SERVER_NAME=domain,
            HTTP_HOST=domain
        )


    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.settings_override = override_settings(
            CACHES=caches_override,
            RATELIMIT_USE_CACHE="default",
            CELERY_TASK_ALWAYS_EAGER=True,
            CELERY_TASK_EAGER_PROPAGATES=True,
            CELERY_BROKER_URL='memory://',
            CELERY_RESULT_BACKEND='cache+memory://',
        )
        cls.settings_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.settings_override.disable()
        super().tearDownClass()
