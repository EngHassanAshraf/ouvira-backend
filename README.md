# Ouvira — Multi-Tenant Backend API

A multi-tenant Django backend providing authentication, RBAC, company management, and audit logging. Built with Django REST Framework and designed for secure, scalable enterprise applications.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | Django 5.2.9 + DRF 3.16.1 |
| Auth | JWT (simplejwt) + OTP (pyotp) + 2FA |
| Database | PostgreSQL 15 |
| Cache | Redis |
| Multi-tenancy | django-tenants (schema isolation) |
| API Docs | Swagger / ReDoc (drf-yasg) |
| Container | Docker & Docker Compose |
| Python | 3.10 |
| Integrations | Twilio SMS, Cloudflare Turnstile |

## Architecture

```
backend/
├── config/                         # Configuration
│   ├── settings/
│   │   ├── base.py                # Shared settings
│   │   ├── local.py               # Dev (DEBUG, CORS open)
│   │   └── production.py          # Prod (SSL, HSTS, CORS whitelist)
│   ├── urls.py                    # Root URL routing
│   ├── asgi.py / wsgi.py          # Entry points (DJANGO_ENV-based)
│
├── apps/
│   ├── access_control/            # RBAC: roles, permissions, invitations
│   │   ├── models/                # Permission, Role, RolePermission, UserCompany, etc.
│   │   ├── services/              # Service layer (business logic)
│   │   ├── api/                   # Serializers, views, URLs
│   │   └── permissions.py
│   │
│   ├── audit/                     # Activity logs, security logs, notifications
│   │   ├── models/
│   │   ├── services/              # NotificationService, ActivityLogService, SecurityAuditLogService
│   │   ├── api/
│   │   └── signals.py
│   │
│   ├── company/                   # Company CRUD, settings, hierarchy
│   │   ├── models/
│   │   ├── services/              # CompanyService, CompanySettingsService
│   │   ├── api/
│   │   └── permissions.py         # IsCompanyOwner, IsCompanyAdmin
│   │
│   ├── identity/
│   │   ├── account/               # User model, profile, user listing
│   │   │   ├── models/
│   │   │   ├── services/          # AccountService
│   │   │   └── api/
│   │   └── auth_app/              # Signup, login, OTP, 2FA, tokens
│   │       ├── services/          # AuthService, OTPService, TwoFAService, TokenService
│   │       └── api/
│   │
│   ├── tenant/                    # Multi-tenancy middleware & models
│   ├── core/                      # Base models, utilities
│   └── shared/                    # Shared exceptions, messages
│
├── manage.py                      # DJANGO_ENV-based settings selection
└── requirements.txt
```

### Layered Architecture

```
Request → Middleware (Tenant) → View → Service Layer → Model
                                  ↓
                             Serializer (validation)
                                  ↓
                             Permission (RBAC)
```

Each app follows: **Models → Services → Serializers → Views → URLs**

## Setup & Installation

### Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for local dev without Docker)

### 1. Environment

```bash
cp .env.example .env
# Edit .env with your values
```

Key variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `DJANGO_ENV` | Settings module (`local` or `production`) | `local` |
| `SECRET_KEY` | Django secret key | **Required** |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost` |
| `TENANT_BASE_DOMAIN` | Base domain for tenant routing | `localhost` |
| `POSTGRES_DB` | Database name | `ouvira_db` |
| `CORS_ALLOWED_ORIGINS` | Production CORS whitelist | — |
| `CSRF_TRUSTED_ORIGINS` | Production CSRF origins | — |

### 2. Docker (Recommended)

```bash
docker compose up --build -d
docker compose exec backend python manage.py createsuperuser
```

Services:
- **Backend API**: `http://localhost:8000`
- **Swagger UI**: `http://localhost:8000/swagger/`
- **ReDoc**: `http://localhost:8000/redoc/`
- **Admin**: `http://localhost:8000/admin/`

### 3. Local (Without Docker)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## API Endpoints

All authenticated endpoints require `Authorization: Bearer <token>` and `X-Tenant: <subdomain>` headers.

### Authentication — `api/auth/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/signup/` | None | Start signup (sends OTP) |
| POST | `/api/auth/resent-otp/` | None | Resend OTP |
| POST | `/api/auth/finalize-signin/` | None | Complete signup (email + password) |
| POST | `/api/auth/login/` | None | Login (email or phone) |
| POST | `/api/auth/logout/` | Bearer | Logout (blacklist token) |
| POST | `/api/auth/token/refresh/` | None | Refresh access token |
| POST | `/api/auth/settings_enable-2fa/` | Bearer | Enable 2FA (TOTP) |
| POST | `/api/auth/login-2fa-verify-code/` | None | Verify 2FA code |
| POST | `/api/auth/login-2fa-verify-backup/` | None | Verify 2FA backup code |
| POST | `/api/auth/otp/send/` | None | Send OTP (email/SMS) |
| POST | `/api/auth/otp/verify/` | None | Verify OTP |
| POST | `/api/auth/password/forgot/` | None | Send password reset link |
| GET | `/api/auth/password/validate-reset-token/` | None | Validate reset token |
| POST | `/api/auth/password/reset/` | None | Reset password with token |
| POST | `/api/auth/password/change/` | Bearer | Change password (known password) |

### Access Control — `api/access-control/`

| Method | Endpoint | Auth |
|--------|----------|------|
| GET, POST | `/api/access-control/permissions/` | Admin |
| GET, PUT, PATCH, DELETE | `/api/access-control/permissions/{id}/` | Admin |
| GET, POST | `/api/access-control/roles/` | Admin |
| GET, PUT, PATCH, DELETE | `/api/access-control/roles/{id}/` | Admin |
| GET, POST | `/api/access-control/role-permissions/` | Admin |
| GET, DELETE | `/api/access-control/role-permissions/{id}/` | Admin |
| GET, POST | `/api/access-control/user-companies/` | Admin |
| GET, PUT, DELETE | `/api/access-control/user-companies/{id}/` | Admin |
| GET, POST | `/api/access-control/user-company-roles/` | Admin |
| GET, DELETE | `/api/access-control/user-company-roles/{id}/` | Admin |
| GET, POST | `/api/access-control/invitations/` | Admin |
| GET, PUT, DELETE | `/api/access-control/invitations/{id}/` | Admin |
| POST | `/api/access-control/invitations/accept/` | Bearer |
| POST | `/api/access-control/invitations/{id}/revoke/` | Admin |
| POST | `/api/access-control/invitations/{id}/resend/` | Admin |

### Company — `api/company/`

| Method | Endpoint | Auth |
|--------|----------|------|
| GET, POST | `/api/company/` | Bearer |
| GET, PUT, PATCH | `/api/company/{id}/` | Bearer / Admin |
| DELETE | `/api/company/{id}/` | Owner |
| GET, PUT, PATCH | `/api/company/{id}/settings/` | Bearer / Admin |

### Account — `api/account/`

| Method | Endpoint | Auth |
|--------|----------|------|
| GET, PUT, PATCH | `/api/account/profile/` | Bearer |
| GET | `/api/account/users/` | Admin |
| GET | `/api/account/session-tests/` | Bearer / Admin |

### Audit — `api/audit/`

| Method | Endpoint | Auth |
|--------|----------|------|
| GET | `/api/audit/notifications/` | Bearer |
| POST | `/api/audit/notifications/mark-read/` | Bearer |
| GET | `/api/audit/activity-logs/` | Admin |
| GET | `/api/audit/activity-logs/my/` | Bearer |
| GET | `/api/audit/security-logs/` | Bearer |

### Rate Limits

| Scope | Limit |
|-------|-------|
| Anonymous | 200/day |
| Authenticated | 1000/day |
| Login | 5/min |
| OTP Verify & 2FA | 5/min |
| OTP Send | 1/min |
| Token Refresh | 20/min |
| Password Forgot | 3/hour |
| Password Change | 10/hour |

## Settings Modes

| Setting | Local (`DJANGO_ENV=local`) | Production (`DJANGO_ENV=production`) |
|---------|---------------------------|--------------------------------------|
| `DEBUG` | `True` | `False` |
| `ALLOWED_HOSTS` | `["*"]` | From env var |
| `CORS` | Allow all origins | Whitelist only |
| `SSL` | Off | Enforced (HSTS 1yr) |
| `SECRET_KEY` | Any | Validated (rejects insecure) |
| `Email` | Console backend | Production backend |

## Useful Commands

```bash
# Logs
docker compose logs -f backend

# Django shell
docker compose exec backend python manage.py shell

# System check
docker compose exec backend python manage.py check

# Stop services
docker compose down

# Reset (delete all data)
docker compose down -v
```

## Contributing

1. Create feature branch: `git checkout -b feature/feature-name`
2. Follow the layered architecture: Models → Services → Serializers → Views → URLs
3. Add audit logging for sensitive operations
4. Include migrations for model changes
5. Update API documentation
