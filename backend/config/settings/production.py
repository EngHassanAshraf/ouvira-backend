"""
Production settings.
"""
import sys
from .base import *
from corsheaders.defaults import default_headers

DEBUG = False

# Validate SECRET_KEY is not the Django insecure default
if SECRET_KEY and "django-insecure" in SECRET_KEY:
    print(
        "FATAL: Using insecure SECRET_KEY in production! "
        "Generate a proper key: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\"",
        file=sys.stderr,
    )
    sys.exit(1)

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(",")

# CORS — whitelist only trusted origins
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
CORS_ALLOW_HEADERS = [
    *default_headers,
    "x-tenant",
]

# CSRF — trust your frontend domains
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}

# Security hardening
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# If behind Nginx / Cloudflare / Proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")

