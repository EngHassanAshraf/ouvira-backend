# Ouvira — Multi-Tenant Enterprise Backend API

A comprehensive multi-tenant Django backend providing authentication, RBAC, company management, HRIS (Human Resources Information System), recruitment, and audit logging. Built with Django REST Framework and designed for secure, scalable enterprise applications.

## 🎯 Project Overview

Ouvira is an enterprise-grade backend system that enables organizations to:
- Manage multi-tenant SaaS deployments with schema isolation
- Handle secure user authentication with JWT, OTP, and 2FA
- Implement fine-grained role-based access control (RBAC)
- Manage companies, employees, departments, and positions
- Run complete recruitment workflows (hiring, candidates, interviews, job offers)
- Track attendance and employee records
- Maintain comprehensive audit logs for compliance

**Target Users:** Enterprise organizations requiring a scalable, secure, multi-tenant backend with HR capabilities.

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|------------|
| **Framework** | Django 5.2.9 + DRF 3.16.1 |
| **Auth** | JWT (simplejwt 5.5.1) + OTP (pyotp 2.9.0) + 2FA (TOTP) |
| **Database** | PostgreSQL 15 + psycopg2-binary 2.9.11 |
| **Cache/Broker** | Redis 7.4.0 (caching + Celery broker) |
| **Multi-tenancy** | django-tenants 3.10.1 (schema isolation) |
| **API Docs** | Swagger / ReDoc (drf-yasg 1.21.11) |
| **Container** | Docker & Docker Compose |
| **Python** | 3.10 |
| **Task Queue** | Celery 5.6.3 + django-celery-beat 2.9.0 |
| **CI/CD** | GitHub Actions (lint, test, docker, security) |
| **Integrations** | Twilio 9.10.4, Vonage 4.7.2, Resend (anymail 13.0), Cloudflare Turnstile |
| **Geo/IP** | geoip2 5.1.0 + django-ipware 7.0.1 |

---

## 🏗 Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│                    (Web/Mobile Applications)                     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                      API Gateway                                 │
│              (CORS, CSRF, Rate Limiting)                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Tenant Middleware                             │
│            (Schema routing based on X-Tenant header)             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                     View Layer                                   │
│         (ViewSet, Serializers, Permissions, Throttling)          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Service Layer                                 │
│              (Business Logic, External APIs)                     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                     Model Layer                                  │
│         (Django ORM, Soft Delete, Audit Tracking)                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Database Layer                                │
│    PostgreSQL (Shared Schema + Tenant Schemas) + Redis Cache     │
└─────────────────────────────────────────────────────────────────┘
```

### Module Breakdown

```
backend/apps/
├── identity/
│   ├── account/           # User model, profile, user listing
│   └── auth_app/          # Signup, login, OTP, 2FA, tokens, password management
│
├── access_control/
│   ├── models/            # Permission, Role, RolePermission, UserCompany, Invitation
│   ├── services/          # RBAC business logic
│   └── api/               # CRUD endpoints for access control
│
├── company/
│   ├── models/            # Company, CompanySettings
│   ├── services/          # Company management logic
│   └── api/               # Company CRUD endpoints
│
├── hris/
│   ├── hris_core/         # Employee, Department, Position, Location, Organization
│   ├── leave_management/  # Leave requests and approvals
│   ├── recruitment/       # Hiring requests, candidates, job applications, interviews
│   ├── travel_management/ # Travel requests and approvals
│   ├── expense_management/# Expense tracking and approvals
│   ├── performance/       # Performance reviews and goals
│   ├── termination/       # Employee offboarding
│   └── analytics/         # HR analytics and reporting
│
├── audit/
│   ├── models/            # ActivityLog, SecurityAuditLog, Notification
│   ├── services/          # Logging and notification services
│   └── api/               # Audit log and notification endpoints
│
├── tenant/
│   ├── models/            # Tenant, Domain
│   └── middleware/        # Tenant routing middleware
│
├── core/                  # Base models, utilities
├── shared/                # Shared exceptions, messages
└── notifications/         # Notification preferences
```

### API Structure

All endpoints are versioned under `/api/v1/`:

| Domain | Base Path |
|--------|-----------|
| Authentication & 2FA | `/api/v1/auth/` |
| User account & profile | `/api/v1/account/` |
| Roles, permissions, invitations | `/api/v1/access-control/` |
| Company management | `/api/v1/company/` |
| HRIS (employees, departments, attendance) | `/api/v1/hris/core/` |
| Recruitment pipeline | `/api/v1/hris/recruitment/` |
| Leave management | `/api/v1/hris/leave/` |
| Expense management | `/api/v1/hris/expense/` |
| Travel management | `/api/v1/hris/travel/` |
| Performance reviews | `/api/v1/hris/performance/` |
| Analytics & reporting | `/api/v1/hris/analytics/` |
| Offboarding & termination | `/api/v1/hris/termination/` |
| Audit logs & notifications | `/api/v1/audit/` |

See [api_documentation.md](api_documentation.md) for full endpoint reference.

---

## ✨ Features

### Authentication & Security
- JWT-based authentication with access/refresh tokens
- OTP verification (email/SMS)
- Two-factor authentication (TOTP with backup codes)
- Password reset via email
- Session management and token blacklisting
- Cloudflare Turnstile integration

### Multi-Tenancy
- Schema-based tenant isolation
- Automatic tenant routing via X-Tenant header
- Shared and tenant-specific tables
- Tenant-aware queries

### Access Control (RBAC)
- Custom permissions per module
- Role-based access control
- User-company associations
- Invitation system with expiry

### Company Management
- Company CRUD operations
- Company settings configuration
- Hierarchy management

### HRIS (Human Resources)
- **Employee Management**: Full employee profiles with personal and professional details
- **Department Management**: Hierarchical department structure
- **Position Management**: Job positions with reporting structure
- **Location Management**: Office locations and addresses
- **Attendance Tracking**: Clock-in/clock-out records

### Recruitment
- **Hiring Requests**: Manager approval workflow
- **Candidate Management**: Candidate profiles and tracking
- **Job Applications**: Application processing
- **Interviews**: Interview scheduling and feedback
- **Job Offers**: Offer generation and onboarding

### Audit & Compliance
- Activity logging for all operations
- Security audit logs
- Notification system
- Compliance tracking

---

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.10+ (for local dev without Docker)
- PostgreSQL 15 (for local dev without Docker)
- Redis (for local dev without Docker)

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/EngHassanAshraf/ouvira-backend.git
cd ouvira-backend

# Copy environment file
cp .env.example .env

# Edit .env with your values
```

### 2. Environment Variables

| Variable | Purpose | Default | Required |
|----------|---------|---------|----------|
| `DJANGO_ENV` | Settings module (`local` or `production`) | `local` | No |
| `SECRET_KEY` | Django secret key | — | **Yes** |
| `DEBUG` | Debug mode | `False` | No |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost` | No |
| `TENANT_BASE_DOMAIN` | Base domain for tenant routing | `localhost` | No |
| `POSTGRES_DB` | Database name | `ouvira_db` | No |
| `POSTGRES_USER` | Database user | `admin_user` | No |
| `POSTGRES_PASSWORD` | Database password | — | **Yes** |
| `DB_HOST` | Database host | `db` | No |
| `DB_PORT` | Database port | `5432` | No |
| `CORS_ALLOWED_ORIGINS` | Production CORS whitelist | — | No |
| `CSRF_TRUSTED_ORIGINS` | Production CSRF origins | — | No |

### 3. Docker (Recommended)

```bash
# Build and start services
docker compose up --build -d

# Create superuser
docker compose exec backend python manage.py createsuperuser

# View logs
docker compose logs -f backend
```

**Services available:**

| Service | URL |
|---------|-----|
| Backend API | `http://localhost:8000` |
| API Root | `http://localhost:8000/` |
| Health Check | `http://localhost:8000/health/` |
| Swagger UI | `http://localhost:8000/swagger/` |
| ReDoc | `http://localhost:8000/redoc/` |
| Admin | `http://localhost:8000/admin/` |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |

### 4. Local Development (Without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
cd backend
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

---

## 📁 Project Structure

```
ouvira-backend/
├── backend/
│   ├── config/                     # Django configuration
│   │   ├── settings/
│   │   │   ├── base.py            # Shared settings
│   │   │   ├── local.py           # Development settings
│   │   │   └── production.py      # Production settings
│   │   ├── urls.py                # Root URL routing
│   │   ├── wsgi.py                # WSGI entry point
│   │   ├── asgi.py                # ASGI entry point
│   │   ├── celery.py              # Celery configuration
│   │   └── middleware.py          # Custom middleware
│   │
│   ├── apps/                       # Application modules
│   │   ├── identity/              # Authentication & accounts
│   │   ├── access_control/        # RBAC
│   │   ├── company/               # Company management
│   │   ├── hris/                  # HRIS modules
│   │   ├── audit/                 # Audit logging
│   │   ├── tenant/                # Multi-tenancy
│   │   ├── core/                  # Base utilities
│   │   └── shared/                # Shared components
│   │
│   ├── manage.py                  # Django management
│   ├── gunicorn.conf.py           # Gunicorn configuration
│   └── requirements.txt           # Python dependencies
│
├── docker/
│   ├── Dockerfile                 # Multi-stage Docker build
│   └── entrypoint.sh              # Container entrypoint
│
├── .github/
│   └── workflows/
│       ├── ci.yml                 # CI pipeline (lint, test, security)
│       └── deploy.yml             # CD pipeline (staging, production)
│
├── docker-compose.yml             # Local development compose
├── railway.toml                   # Railway deployment config
├── .env.example                   # Environment template
└── README.md                      # This file
```

---

## 🔧 Development Workflow

### Branching Strategy

```
main (production)
  └── develop (staging)
        └── feature/* (feature branches)
        └── hotfix/* (urgent fixes)
        └── release/* (release preparation)
```

### Creating a Feature Branch

```bash
# Create feature branch
git checkout -b feature/feature-name

# Make changes and commit
git add .
git commit -m "feat: description of changes"

# Push to remote
git push origin feature/feature-name
```

### Running Tests

```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest apps/identity/tests/test_auth.py
```

### Code Quality

```bash
# Run linting
flake8 backend/

# Check formatting
black --check backend/

# Check imports
isort --check-only backend/
```

### Making Migrations

```bash
# Create migrations after model changes
python manage.py makemigrations

# Review migration file
# Then commit the migration file

# Apply migrations
python manage.py migrate
```

---

## 🚀 Deployment

### CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

**CI Pipeline (on push/PR):**
- Linting (flake8, black, isort)
- Testing (pytest with coverage)
- Docker build validation
- Security scanning (safety, bandit)

**CD Pipeline (on merge to main/develop):**
- Build and push Docker image
- Deploy to staging (develop) or production (main)
- Run migrations
- Health checks

### Environments

| Environment | Branch | URL | Auto-deploy |
|-------------|--------|-----|-------------|
| Development | feature/* | Local | Manual |
| Staging | develop | staging.ouvira.com | Yes |
| Production | main | ouvira.com | After staging validation |

### Deployment Commands

```bash
# Build Docker image
docker build -f docker/Dockerfile -t ouvira-backend:latest .

# Run production container
docker run -d \
  -e DJANGO_ENV=production \
  -e SECRET_KEY=your-secret-key \
  -p 8000:8000 \
  ouvira-backend:latest
```

---

## 📝 Contributing

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/feature-name
   ```

2. **Follow the layered architecture:**
   - Models → Services → Serializers → Views → URLs

3. **Add tests for new functionality:**
   ```bash
   pytest apps/your_module/tests/
   ```

4. **Include migrations for model changes:**
   ```bash
   python manage.py makemigrations
   ```

5. **Add audit logging for sensitive operations:**
   ```python
   from apps.audit.services import ActivityLogService
   ActivityLogService.log_action(user, "action_type", details)
   ```

6. **Update API documentation** if endpoints change

7. **Create a pull request** with:
   - Clear description of changes
   - Test results
   - Screenshots (if UI changes)

### Code Standards

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for public methods
- Keep functions small and focused
- Use service layer for business logic

---

## 📄 License

Proprietary - All rights reserved.

---

## 📞 Support

For questions or issues:
- **Documentation**: `/swagger/` or `/redoc/`
- **Admin Panel**: `/admin/`
- **GitHub Issues**: [Report issues](https://github.com/EngHassanAshraf/ouvira-backend/issues)