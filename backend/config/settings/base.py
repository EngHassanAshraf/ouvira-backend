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
        "otp_verify": "5/m",
        "twofa_verify": "5/m",
        "refresh": "20/m",
        "enable_2fa": "10/h",
        "register_owner": "3/h",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
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


# === EMAIL SERVICE CONF ===
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587)) 
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")


# === TURNSTILE ===
TURNSTILE_SITE_KEY = os.getenv("TURNSTILE_SITE_KEY")
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY")
