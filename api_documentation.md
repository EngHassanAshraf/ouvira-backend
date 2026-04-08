# Ouvira API Documentation

**Version:** v1
**Base URL:** `http://localhost:8000` (development) | `https://api.ouvira.com` (production)
**Content-Type:** `application/json`

---

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [Endpoints](#endpoints)
   - [Auth](#1-auth--apiv1auth)
   - [Account](#2-account--apiv1account)
   - [Access Control](#3-access-control--apiv1access-control)
   - [Company](#4-company--apiv1company)
   - [HRIS Core](#5-hris-core--apiv1hriscore)
   - [Recruitment](#6-recruitment--apiv1hrisrecruitment)
   - [Audit](#7-audit--apiv1audit)
5. [Utility Endpoints](#utility-endpoints)
6. [Pagination](#pagination)
7. [Rate Limiting](#rate-limiting)

---

## API Overview

### Versioning

All endpoints are versioned under `/api/v1/`. Future versions will be available at `/api/v2/` etc. without breaking existing clients.

### Required Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes (authenticated) | `Bearer <access_token>` |
| `X-Tenant` | Yes | Tenant subdomain for schema routing |
| `Content-Type` | Yes (POST/PUT/PATCH) | `application/json` |

### Response Format

**Single resource:**
```json
{
  "id": 1,
  "field": "value",
  "created_at": "2026-01-15T10:00:00Z"
}
```

**Paginated list:**
```json
{
  "count": 100,
  "next": "https://api.ouvira.com/api/v1/endpoint/?page=2",
  "previous": null,
  "results": []
}
```

**Error:**
```json
{ "detail": "Error message" }
```

**Validation error:**
```json
{ "field_name": ["Error message for this field"] }
```

---

## Authentication

### Token Lifecycle

| Token | Lifetime | Purpose |
|-------|----------|---------|
| Access Token | 15 minutes | Authenticate API requests |
| Refresh Token | 7 days | Obtain new access token |

### Flows

**Signup:** `POST /api/v1/auth/signup/` → OTP sent → `POST /api/v1/auth/finalize-signin/` → tokens

**Login:** `POST /api/v1/auth/login/` → tokens (or 2FA challenge) → `POST /api/v1/auth/2fa/verify/code/` → tokens

**Token usage:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Error Handling

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request — invalid input |
| 401 | Unauthorized — missing or expired token |
| 403 | Forbidden — insufficient permissions |
| 404 | Not Found |
| 429 | Too Many Requests — rate limit hit |
| 500 | Internal Server Error |

---

## Endpoints

### 1. Auth — `/api/v1/auth/`

#### POST `/api/v1/auth/signup/`
**Auth:** None | **Rate:** 3/hour

**Request:**
```json
{
  "full_name": "Hassan Ashraf",
  "primary_mobile": "+201234567890"
}
```
**Response (201):**
```json
{ "message": "OTP sent successfully", "primary_mobile": "+201234567890" }
```

---

#### POST `/api/v1/auth/finalize-signin/`
**Auth:** None | **Rate:** 3/hour

**Request:**
```json
{
  "primary_mobile": "+201234567890",
  "email": "user@example.com",
  "password": "SecureP@ss123"
}
```
**Response (201):**
```json
{
  "message": "Account created successfully",
  "tokens": { "access": "eyJ...", "refresh": "eyJ..." }
}
```

---

#### POST `/api/v1/auth/login/`
**Auth:** None | **Rate:** 5/min

**Request:**
```json
{
  "identifier": "user@example.com",
  "password": "SecureP@ss123",
  "cf_turnstile_response": "<turnstile-token>"
}
```
**Response (200) — no 2FA:**
```json
{
  "tokens": { "access": "eyJ...", "refresh": "eyJ..." },
  "user": { "id": 1, "username": "hassan", "full_name": "Hassan Ashraf", "email": "user@example.com" }
}
```
**Response (200) — 2FA required:**
```json
{ "requires_2fa": true, "session_id": "uuid-session-id" }
```

---

#### POST `/api/v1/auth/logout/`
**Auth:** Bearer Token

**Request:**
```json
{ "refresh": "eyJ..." }
```
**Response (205):**
```json
{ "detail": "Successfully logged out." }
```

---

#### POST `/api/v1/auth/token/refresh/`
**Auth:** None | **Rate:** 20/min

**Request:**
```json
{ "refresh": "eyJ..." }
```
**Response (200):**
```json
{ "access": "eyJ...", "refresh": "eyJ..." }
```

---

#### OTP Endpoints

| Method | Endpoint | Rate | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/otp/send/` | 1/min | Send OTP via email or SMS |
| POST | `/api/v1/auth/otp/verify/` | 5/min | Verify OTP |
| POST | `/api/v1/auth/otp/resend/` | 3/hour | Resend OTP |

**Send/Resend request:**
```json
{ "identifier": "user@example.com" }
```
**Verify request:**
```json
{ "identifier": "user@example.com", "otp": "123456" }
```

---

#### Two-Factor Authentication

| Method | Endpoint | Rate | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/2fa/enable/` | 10/hour | Enable TOTP 2FA |
| POST | `/api/v1/auth/2fa/verify/code/` | 5/min | Verify TOTP code during login |
| POST | `/api/v1/auth/2fa/verify/backup/` | 5/min | Verify backup code during login |

**Enable response (200):**
```json
{
  "secret": "BASE32SECRET",
  "qr_code": "otpauth://totp/Ouvira:user@example.com?secret=BASE32SECRET&issuer=Ouvira",
  "backup_codes": ["code1", "code2", "code3", "code4", "code5"]
}
```

**Verify code request:**
```json
{ "session_id": "uuid-session-id", "code": "123456" }
```

---

#### Password Management

| Method | Endpoint | Rate | Auth | Description |
|--------|----------|------|------|-------------|
| POST | `/api/v1/auth/password/forgot/` | 3/hour | None | Request reset link |
| GET | `/api/v1/auth/password/validate-reset-token/` | — | None | Validate reset token (`?token=...`) |
| POST | `/api/v1/auth/password/reset/` | 3/hour | None | Reset with token |
| POST | `/api/v1/auth/password/change/` | 10/hour | Bearer | Change current password |

**Reset request:**
```json
{ "token": "b4b2c1d3...", "new_password": "NewSecureP@ss123!" }
```
**Change request:**
```json
{ "old_password": "CurrentP@ss123!", "new_password": "NewSecureP@ss123!" }
```

---

### 2. Account — `/api/v1/account/`

#### GET/PUT/PATCH `/api/v1/account/profile/`
**Auth:** Bearer Token

**Response (200):**
```json
{
  "id": 1,
  "username": "hassan",
  "full_name": "Hassan Ashraf",
  "email": "user@example.com",
  "primary_mobile": "+201234567890",
  "email_verified": true,
  "phone_verified": true,
  "account_uid": "USR-1234ABCD",
  "is_2fa_enabled": false,
  "two_fa_type": "AUTHENTICATOR",
  "date_joined": "2026-01-15T10:00:00Z",
  "last_login": "2026-04-08T10:00:00Z"
}
```

---

#### GET `/api/v1/account/users/`
**Auth:** Bearer + Admin | **Query:** `?company=<id>`

Returns paginated list of active users.

---

### 3. Access Control — `/api/v1/access-control/`

#### Permissions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/access-control/permissions/` | List / create |
| GET/PUT/PATCH/DELETE | `/api/v1/access-control/permissions/{id}/` | Detail / update / delete |

**Object:**
```json
{
  "id": 1,
  "code": "hris_recruitment.view_hiring_request",
  "module": "Recruitment",
  "description": "Can view hiring requests"
}
```

---

#### Roles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/access-control/roles/` | List / create |
| GET/PUT/PATCH/DELETE | `/api/v1/access-control/roles/{id}/` | Detail / update / delete |

**Object:**
```json
{
  "id": 1,
  "role": "HR Manager",
  "desc": "Full HR access",
  "company": 1,
  "is_system_role": false
}
```

---

#### Role Permissions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/access-control/role-permissions/` | List / assign |
| GET/DELETE | `/api/v1/access-control/role-permissions/{id}/` | Detail / remove |

---

#### User Companies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/access-control/user-companies/` | List / associate |
| GET/PUT/PATCH/DELETE | `/api/v1/access-control/user-companies/{id}/` | Detail / update / remove |

---

#### User Company Roles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/access-control/user-company-roles/` | List / assign |
| GET/DELETE | `/api/v1/access-control/user-company-roles/{id}/` | Detail / remove |

---

#### Invitations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/access-control/invitations/` | List / create |
| POST | `/api/v1/access-control/invitations/accept/` | Accept invitation |
| GET/PUT/PATCH | `/api/v1/access-control/invitations/{id}/` | Detail / update |
| POST | `/api/v1/access-control/invitations/{id}/revoke/` | Revoke |
| POST | `/api/v1/access-control/invitations/{id}/resend/` | Resend |

**Object:**
```json
{
  "id": 1,
  "email": "newuser@example.com",
  "company": 1,
  "role": 2,
  "status": "pending",
  "expires_at": "2026-05-01T00:00:00Z"
}
```

---

### 4. Company — `/api/v1/company/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/company/` | List / create |
| GET/PUT/PATCH/DELETE | `/api/v1/company/{id}/` | Detail / update / delete |
| GET/PUT | `/api/v1/company/{id}/settings/` | Get / update settings |

---

### 5. HRIS Core — `/api/v1/hris/core/`

#### Employees

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/hris/core/employees/` | List / create |
| GET/PUT/PATCH/DELETE | `/api/v1/hris/core/employees/{id}/` | Detail / update / soft-delete |
| GET/POST | `/api/v1/hris/core/employees/{id}/employments/` | List / create employment records |
| GET/PUT/PATCH/DELETE | `/api/v1/hris/core/employees/{id}/employments/{eid}/` | Employment detail |
| GET/POST | `/api/v1/hris/core/employees/{id}/attendances/` | List / create attendance |
| GET/PUT/PATCH/DELETE | `/api/v1/hris/core/employees/{id}/attendances/{aid}/` | Attendance detail |

**Employee object:**
```json
{
  "id": 1,
  "employee_id": "EMP-001",
  "first_name": "Ahmed",
  "last_name": "Mohamed",
  "national_id": "1234567890",
  "date_of_birth": "1990-01-15",
  "gender": "M",
  "marital_status": "M",
  "contact_number": "+966501234567",
  "personal_email": "ahmed@example.com",
  "company": 1,
  "department": 1,
  "location": 1
}
```

**Attendance object:**
```json
{
  "id": 1,
  "employee": 1,
  "date": "2026-04-08",
  "check_in_time": "09:00:00",
  "check_out_time": "17:00:00",
  "status": "present"
}
```

---

#### Departments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/hris/core/departments/` | List / create |
| GET/PUT/PATCH/DELETE | `/api/v1/hris/core/departments/{id}/` | Detail / update / soft-delete |

---

#### Job Titles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/hris/core/job-titles/` | List / create |
| GET/PUT/PATCH/DELETE | `/api/v1/hris/core/job-titles/{id}/` | Detail / update / soft-delete |

---

#### Positions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/hris/core/positions/` | List / create |
| GET/PUT/PATCH/DELETE | `/api/v1/hris/core/positions/{id}/` | Detail / update / soft-delete |

---

#### Locations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/hris/core/locations/` | List / create |
| GET/PUT/PATCH/DELETE | `/api/v1/hris/core/locations/{id}/` | Detail / update / soft-delete |

---

### 6. Recruitment — `/api/v1/hris/recruitment/`

All recruitment endpoints use DRF `DefaultRouter` and support standard CRUD plus custom actions.

#### Hiring Requests

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/hris/recruitment/hiring-requests/` | List / create |
| GET/PUT/PATCH/DELETE | `/api/v1/hris/recruitment/hiring-requests/{id}/` | Detail / update / delete |
| POST | `/api/v1/hris/recruitment/hiring-requests/{id}/submit/` | Submit for approval |
| POST | `/api/v1/hris/recruitment/hiring-requests/{id}/approve/` | Approve (with role_type) |

**Object:**
```json
{
  "id": 1,
  "company": 1,
  "department": 1,
  "job_title": 1,
  "vacancies": 2,
  "purpose": "Expansion of engineering team",
  "status": "draft",
  "created_by": 1
}
```

---

#### Job Advertisements

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/hris/recruitment/job-advertisements/` | List / create |
| GET/PUT/PATCH/DELETE | `/api/v1/hris/recruitment/job-advertisements/{id}/` | Detail / update / delete |
| POST | `/api/v1/hris/recruitment/job-advertisements/{id}/publish/` | Publish ad |
| POST | `/api/v1/hris/recruitment/job-advertisements/{id}/close/` | Close ad |

**Object:**
```json
{
  "id": 1,
  "hiring_request": 1,
  "title": "Senior Backend Engineer",
  "description": "...",
  "requirements": "...",
  "skills": ["Python", "Django", "PostgreSQL"],
  "responsibilities": "...",
  "deadline": "2026-06-30",
  "platforms": ["internal", "linkedin"],
  "status": "draft"
}
```

---

#### Candidates

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/hris/recruitment/candidates/` | List / create |
| GET/PUT/PATCH/DELETE | `/api/v1/hris/recruitment/candidates/{id}/` | Detail / update / delete |

**Object:**
```json
{
  "id": 1,
  "first_name": "Sara",
  "last_name": "Ali",
  "email": "sara@example.com",
  "phone": "+201234567890",
  "linkedin_url": "https://linkedin.com/in/sara-ali",
  "source": "LinkedIn",
  "company": 1
}
```

---

#### Job Applications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/hris/recruitment/applications/` | List / create |
| GET/PUT/PATCH/DELETE | `/api/v1/hris/recruitment/applications/{id}/` | Detail / update / delete |
| POST | `/api/v1/hris/recruitment/applications/{id}/move-to-stage/` | Advance pipeline stage |

**Object:**
```json
{
  "id": 1,
  "candidate": 1,
  "job_advertisement": 1,
  "status": "applied",
  "classification": "none",
  "applied_at": "2026-04-08T10:00:00Z"
}
```

**Stage values:** `applied` → `phone_screening` → `interview` → `offer` → `hired` / `rejected`

---

#### Interviews

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/hris/recruitment/interviews/` | List / schedule |
| GET/PUT/PATCH/DELETE | `/api/v1/hris/recruitment/interviews/{id}/` | Detail / update / delete |
| POST | `/api/v1/hris/recruitment/interviews/{id}/record-result/` | Record scoring |

**Object:**
```json
{
  "id": 1,
  "application": 1,
  "interview_type": "personal",
  "interview_date": "2026-05-01T10:00:00Z",
  "interviewers": [1, 2],
  "status": "scheduled",
  "average_score": 0.0,
  "scoring_data": {}
}
```

---

#### Candidate Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/hris/recruitment/documents/` | List / upload |
| GET/PUT/PATCH/DELETE | `/api/v1/hris/recruitment/documents/{id}/` | Detail / update / delete |

**doc_type values:** `id_copy`, `qualification`, `military_status`, `personal_photo`, `police_clearance`, `other`

---

#### Job Offers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/hris/recruitment/offers/` | List / create |
| GET/PUT/PATCH/DELETE | `/api/v1/hris/recruitment/offers/{id}/` | Detail / update / delete |
| POST | `/api/v1/hris/recruitment/offers/{id}/accept/` | Accept offer → creates employee record |

**Object:**
```json
{
  "id": 1,
  "application": 1,
  "salary": "25000.00",
  "allowance": "2000.00",
  "benefits": "Health insurance, annual leave",
  "start_date": "2026-06-01",
  "status": "draft"
}
```

---

#### Onboarding

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/hris/recruitment/onboarding/` | List / create |
| GET/PUT/PATCH/DELETE | `/api/v1/hris/recruitment/onboarding/{id}/` | Detail / update / delete |

**Object:**
```json
{
  "id": 1,
  "candidate": 1,
  "tasks": { "workspace_setup": false, "email_created": false, "id_badge": false },
  "status": "not_started"
}
```

---

### 7. Audit — `/api/v1/audit/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/audit/notifications/` | List my notifications |
| POST | `/api/v1/audit/notifications/mark-read/` | Mark notifications as read |
| GET | `/api/v1/audit/activity-logs/` | List all activity logs (admin) |
| GET | `/api/v1/audit/activity-logs/my/` | List my activity logs |
| GET | `/api/v1/audit/security-logs/` | List security audit logs (admin) |

---

## Utility Endpoints

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /` | None | API root — service name, version, links |
| `GET /health/` | None | Liveness probe — status, timestamp |
| `GET /swagger/` | None | Swagger UI |
| `GET /redoc/` | None | ReDoc UI |
| `GET /swagger.json` | None | OpenAPI schema (JSON) |
| `GET /swagger.yaml` | None | OpenAPI schema (YAML) |
| `GET /admin/` | Django session | Django admin panel |

**Health response:**
```json
{
  "status": "ok",
  "service": "ouvira-backend",
  "version": "v1",
  "timestamp": "2026-04-08T10:00:00Z"
}
```

---

## Pagination

All list endpoints return paginated responses.

**Query parameters:**
- `page` — page number (default: 1)
- `page_size` — items per page (default: 20)

```
GET /api/v1/hris/core/employees/?page=2&page_size=50
```

---

## Rate Limiting

| Scope | Limit | Window |
|-------|-------|--------|
| Anonymous | 200 | per day |
| Authenticated | 1000 | per day |
| `login` | 5 | per minute |
| `otp_send` | 1 | per minute |
| `otp_verify` | 5 | per minute |
| `twofa_verify` | 5 | per minute |
| `refresh` | 20 | per minute |
| `signup` | 3 | per hour |
| `finalize_signin` | 3 | per hour |
| `otp_resend` | 3 | per hour |
| `forgot_password` | 3 | per hour |
| `enable_2fa` | 10 | per hour |
| `password_change` | 10 | per hour |
