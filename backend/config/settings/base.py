import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import timedelta

load_dotenv()


FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


# === CORE SETTINGS ===

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG", "False") == "True"

TEST_MODE = os.getenv("TEST_MODE", "False") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# === APPLICATION DEFINITION ===

DEFAULT_APPS = (
)

SHARED_APPS = [    
    "django_tenants",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "apps.tenant",
    "apps.identity.account",
    "apps.identity.auth_app",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",    
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_yasg",
    "apps.company",
    "apps.audit",
    "apps.access_control",
    "django_celery_beat",
    ]

TENANT_CREATED_APPS = (
    "apps.core",

    # hris/modules
    "apps.hris.hris_core",
    'apps.hris.leave_management',
    'apps.hris.recruitment',
    'apps.hris.travel_management',
    'apps.hris.expense_management',
    'apps.hris.performance',
    'apps.hris.termination',
    'apps.hris.analytics',
    'apps.hris.internal_auth',
)

TENANT_THIRD_PARTY = ()

TENANT_APPS = [*TENANT_THIRD_PARTY, *TENANT_CREATED_APPS]

INSTALLED_APPS = [app for app in TENANT_APPS if app not in SHARED_APPS] + list(
    SHARED_APPS
)


# === AUTH ===

AUTH_USER_MODEL = "account.CustomUser"


# === MULTI-TENANCY ===

TENANT_MODEL = "tenant.Tenant"
TENANT_DOMAIN_MODEL = "tenant.Domain"
TENANT_BASE_DOMAIN = os.getenv("TENANT_BASE_DOMAIN", "")

DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)


# === REST FRAMEWORK ===

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "200/d",
        "user": "1000/d",
        "signup": "3/h",
        "finalize_signin": "3/h",
        "login": "5/m",
        "otp_resend": "3/h",
        # 5/m matches the Redis attempt-lock threshold in OTPService.verify().
        # The Redis lock is the primary enforcement (keyed to identifier, not IP).
        # This DRF scope is a secondary IP-level backstop only.
        "otp_verify": "5/m",
        "twofa_verify": "5/m",
        "refresh": "20/m",
        "enable_2fa": "10/h",
        "register_owner": "3/h",
        # New scopes (auth security endpoints)
        "otp_send": "1/m",
        "forgot_password": "3/h",
        "password_change": "10/h",
        # Internal auth
        "internal_login": "10/m",
    },
}

SIMPLE_JWT = {
    "ALGORITHM": "HS256",
    "SIGNING_KEY": os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY"),  # prefer a separate key
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),   # AUTH-001: ≤15min per OWASP ASVS 3.5.1
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}


# === SESSION ===

SESSION_COOKIE_AGE = 30 * 60
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = False


# === MIDDLEWARE ===

MIDDLEWARE = [
    "apps.tenant.middleware.HeaderTenantMainMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# === URL CONFIG ===

ROOT_URLCONF = "config.urls"

APPEND_SLASH = os.getenv("DJANGO_APPEND_SLASH", "True") == "True"


# === TEMPLATES ===

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# === SWAGGER ===

SWAGGER_SETTINGS = {
    "USE_SESSION_AUTH": False,
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT token: Bearer <token>",
        }
    },
}


# === PASSWORD VALIDATION ===

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# === I18N ===

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Cairo"

USE_I18N = True

USE_TZ = True


# === STATIC ===

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# === DEFAULT PK ===

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# === LOGGING ===

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


# === EXTERNAL SERVICE KEYS ===

# === SMS SERVICE CONF ===
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

VONAGE_KEY = os.getenv("VONAGE_KEY")
VONAGE_API_SECRET = os.getenv("VONAGE_API_SECRET")

INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY")


# === EMAIL SERVICE CONF ===
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "")
ANYMAIL = {
    "RESEND_API_KEY": os.getenv("RESEND_API_KEY", "")
}
# EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
# EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587)) 
# EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
# EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")


# === TURNSTILE ===
TURNSTILE_SITE_KEY = os.getenv("TURNSTILE_SITE_KEY")
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY")
TURNSTILE_BYPASS_TOKEN = os.getenv("TURNSTILE_BYPASS_TOKEN", "")


# === CELERY (JSON serializer prevents pickle deserialization attacks) ===
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE

if TEST_MODE:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_DEFAULT_QUEUE = "default"

# Nightly cleanup schedule — use crontab if celery is installed
try:
    from celery.schedules import crontab as _crontab
    _cleanup_schedule = _crontab(hour=3, minute=0)
except ImportError:
    _cleanup_schedule = 86400  # fallback: 24 hours in seconds (celery not yet installed)

CELERY_BEAT_SCHEDULE = {
    "cleanup-expired-auth-records": {
        "task": "apps.identity.auth_app.tasks.cleanup_tasks.cleanup_expired_auth_records",
        "schedule": _cleanup_schedule,
    },
}


# === GEOIP (MaxMind GeoLite2 offline DB path) ===
GEOIP_PATH = os.path.join(BASE_DIR, "geoip", "GeoLite2-City.mmdb")


# === CACHE ===
# Redis is required for correct throttling and OTP lockout behavior in
# multi-worker deployments. The default LocMemCache is per-process and
# does NOT share state across Gunicorn workers or Celery workers.
#
# DRF throttling uses django.core.cache.cache — if this is LocMemCache,
# each worker has its own counter and rate limits are effectively multiplied
# by the number of workers (e.g. 4 workers × 5/min = 20 effective req/min).
#
# OTP attempt locking (Redis-based in OTPService) is already correct, but
# DRF's ScopedRateThrottle for otp_verify is a secondary backstop that also
# needs Redis to be consistent.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://redis:6379/1"),
        # Use DB 1 for cache (DB 0 is Celery broker/result backend)
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "ouvira",
        "TIMEOUT": 300,  # 5 minutes default TTL
    }
}

# Session engine — use cache-backed sessions for multi-worker consistency
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
