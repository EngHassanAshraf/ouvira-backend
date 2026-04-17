"""
Production settings.
"""
import sys
from .base import *
from corsheaders.defaults import default_headers

# Validate SECRET_KEY is not the Django insecure default
if SECRET_KEY and "django-insecure" in SECRET_KEY:
    print(
        "FATAL: Using insecure SECRET_KEY in production! "
        "Generate a proper key: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\"",
        file=sys.stderr,
    )
    sys.exit(1)

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(",")

# Railway healthcheck uses a fixed host — always allow it
ALLOWED_HOSTS += ["healthcheck.railway.app", ".railway.app"]

# CORS — whitelist only trusted origins
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "False") == "True"
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip() and origin.strip() != "*" and "://" in origin.strip()
]
CORS_ALLOW_HEADERS = [
    *default_headers,
    "x-tenant",
    "x-turnstile-bypass",
]

# CSRF — trust your frontend domains
# Values must start with a scheme (https:// or http://) per Django 4.0+
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip() and origin.strip() != "*" and "://" in origin.strip()
]

DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
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

