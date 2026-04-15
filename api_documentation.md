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
   - [Auth (External)](#1-auth-external--apiv1auth)
   - [Internal Auth](#2-internal-auth--apiv1hrisinternalauth)
   - [Account](#3-account--apiv1account)
   - [Access Control](#4-access-control--apiv1access-control)
   - [Company](#5-company--apiv1company)
   - [HRIS Core](#6-hris-core--apiv1hriscore)
   - [Recruitment](#7-recruitment--apiv1hrisrecruitment)
   - [Audit](#8-audit--apiv1audit)
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

### 1. Auth (External) — `/api/v1/auth/`

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

### 2. Internal Auth — `/api/v1/hris/internal/auth/`

Internal authentication for company employees and staff. Separate from the external auth flow — no OTP, no Turnstile, no signup. Returns enriched JWT with company context, employee context, roles, permissions, and a role-based redirect.

**Two auth flows exist:**

| Flow | Endpoint prefix | Who uses it |
|------|----------------|-------------|
| External | `/api/v1/auth/` | Customers, tenant owners, SaaS signup |
| Internal | `/api/v1/hris/internal/auth/` | Employees, HR staff, managers, admins |

---

#### POST `/api/v1/hris/internal/auth/login/`

**Auth:** None | **Rate:** 10/min

Authenticate an internal user. Returns enriched JWT with company context, employee ID, roles, permissions, and a redirect hint.

**Request:**

```json
{
  "identifier": "ahmed@company.com",
  "password": "SecureP@ss123",
  "company_id": 1
}
```

`company_id` is optional. If omitted, the user's primary active company is used. Required only for users who belong to multiple companies.

**Response (200):**

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "id": 1,
    "account_uid": "USR-1234ABCD",
    "email": "ahmed@company.com",
    "full_name": "Ahmed Mohamed",
    "company_id": 1,
    "employee_id": "EMP-001",
    "roles": ["HR_ADMIN"],
    "permissions": ["hr.view_employee", "hr.edit_employee", "hr.approve_leave"],
    "modules": ["hr"]
  },
  "redirect": {
    "module": "hr",
    "path": "/hr/dashboard"
  }
}
```

**JWT access token payload includes:**

| Claim | Type | Description |
|-------|------|-------------|
| `user_id` | int | User primary key |
| `company_id` | int | Resolved company |
| `employee_id` | string \| null | Employee ID string (e.g. `EMP-001`) |
| `roles` | string[] | All active role names for this user+company |
| `permissions` | string[] | Flattened, deduplicated permission codes |
| `modules` | string[] | Accessible module names derived from permissions |
| `token_type` | string | Always `"internal_access"` |

**Error responses:**

| Status | When |
|--------|------|
| 400 | Missing or invalid input fields |
| 401 | Wrong credentials, inactive account, deleted account, no active company |
| 429 | Rate limit exceeded (10/min) |
| 500 | Unexpected server error |

All auth failures return `401` with a generic message — specific failure reasons are never exposed to prevent user enumeration.

**Account lockout:** 5 consecutive failed attempts → 30-minute lockout. Returns `401` with lockout message.

---

#### POST `/api/v1/hris/internal/auth/logout/`

**Auth:** Bearer Token (internal access token)

Blacklist the refresh token. Uses the same SimpleJWT blacklist as the external flow.

**Request:**

```json
{ "refresh_token": "eyJ..." }
```

**Response (205):**

```json
{ "detail": "Logged out successfully." }
```

---

#### GET `/api/v1/hris/internal/auth/me/`

**Auth:** Bearer Token (internal access token)

Returns the current user's context decoded directly from the JWT — zero database queries.

**Response (200):**

```json
{
  "user_id": 1,
  "company_id": 1,
  "employee_id": "EMP-001",
  "roles": ["HR_ADMIN"],
  "permissions": ["hr.view_employee", "hr.edit_employee"],
  "modules": ["hr"],
  "token_type": "internal_access"
}
```

---

#### Role → Module Redirect Map

The `redirect` object in the login response maps the user's highest-priority role to a default frontend route. Priority order (highest first):

| Role | Module | Default Path |
|------|--------|-------------|
| `super_admin` / `system_admin` / `admin` | `admin` | `/admin/dashboard` |
| `finance_director` | `finance` | `/finance/dashboard` |
| `hr_admin` / `hr_manager` | `hr` | `/hr/dashboard` |
| `payroll_admin` / `payroll_manager` | `payroll` | `/payroll/overview` |
| `sales_director` / `crm_admin` | `sales` | `/sales/dashboard` |
| `procurement_manager` | `procurement` | `/procurement/dashboard` |
| `inventory_manager` / `warehouse_manager` | `inventory` | `/inventory/dashboard` |
| `pmo_director` | `projects` | `/projects/dashboard` |
| `it_manager` / `it_admin` | `it` | `/it/dashboard` |
| `legal_manager` | `legal` | `/legal/dashboard` |
| `marketing_director` | `marketing` | `/marketing/dashboard` |
| `operations_director` / `operations_manager` | `operations` | `/operations/dashboard` |
| `hr_employee` / `hr_staff` | `hr` | `/hr/employees` |
| `payroll_staff` | `payroll` | `/payroll/runs` |
| `recruiter` / `recruitment_manager` | `recruitment` | `/recruitment/pipeline` |
| `direct_manager` / `department_manager` / `manager` | `hr` | `/hr/team` |
| `employee` (default) | `self` | `/self-service/dashboard` |

The frontend may override the redirect — the `redirect` field is a hint, not a hard redirect.

---

#### Internal Login Audit

Every login attempt (success, failure, lockout) is recorded in `InternalLoginAttempt`:

| Field | Description |
|-------|-------------|
| `identifier` | Email or username submitted |
| `outcome` | `success` \| `failure` \| `locked` |
| `failure_reason` | Machine-readable reason (never exposed to client) |
| `user` | Resolved user (null if not found) |
| `company_id` | Resolved company (null if not resolved) |
| `ip_address` | Client IP |
| `user_agent` | HTTP User-Agent |
| `created_at` | Timestamp |

---

### 3. Account — `/api/v1/account/`

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

### 4. Access Control — `/api/v1/access-control/`

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

### 5. Company — `/api/v1/company/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/company/` | List / create |
| GET/PUT/PATCH/DELETE | `/api/v1/company/{id}/` | Detail / update / delete |
| GET/PUT | `/api/v1/company/{id}/settings/` | Get / update settings |

---

### 6. HRIS Core — `/api/v1/hris/core/`

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

### 7. Recruitment — `/api/v1/hris/recruitment/`

All recruitment endpoints use DRF `DefaultRouter` and support standard CRUD plus custom actions.

#### Hiring Requests

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/hris/recruitment/hiring-requests/` | List / create |
| GET | `/api/v1/hris/recruitment/hiring-requests/{id}/` | Detail |
| PUT/PATCH | `/api/v1/hris/recruitment/hiring-requests/{id}/` | Update — **draft only** |
| DELETE | `/api/v1/hris/recruitment/hiring-requests/{id}/` | Soft delete — **draft only** |
| POST | `/api/v1/hris/recruitment/hiring-requests/{id}/submit/` | Submit for approval |
| POST | `/api/v1/hris/recruitment/hiring-requests/{id}/approve/` | Approve one step (`role_type` required) |
| POST | `/api/v1/hris/recruitment/hiring-requests/{id}/reject/` | Reject at any step (`role_type` + `reason` required) |
| POST | `/api/v1/hris/recruitment/hiring-requests/{id}/cancel/` | Cancel draft or submitted request |

**Edit rules:**
- `PUT/PATCH` only allowed on `draft` requests. Editable fields: `job_title`, `department`, `vacancies`, `purpose`.
- `DELETE` only allowed on `draft` requests (soft delete). Cancel first if submitted.
- `cancel` allowed on `draft` or `submitted`. Terminal — cannot be undone.

**Approve body:**
```json
{ "role_type": "employee|hr_employee|direct_manager", "note": "optional" }
```

**Cancel body:**
```json
{ "reason": "Budget freeze — position postponed" }
```

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
  "created_by": 1,
  "approvals": []
}
```

**Status lifecycle:** `draft` → `submitted` → `approved` | `rejected`

---

#### Job Advertisements

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/hris/recruitment/job-advertisements/` | List / create |
| GET | `/api/v1/hris/recruitment/job-advertisements/{id}/` | Detail |
| PUT/PATCH | `/api/v1/hris/recruitment/job-advertisements/{id}/` | Update (state-dependent rules) |
| DELETE | `/api/v1/hris/recruitment/job-advertisements/{id}/` | Soft delete — **draft only** |
| POST | `/api/v1/hris/recruitment/job-advertisements/{id}/publish/` | Publish draft ad |
| POST | `/api/v1/hris/recruitment/job-advertisements/{id}/close/` | Close published ad |
| POST | `/api/v1/hris/recruitment/job-advertisements/{id}/reopen/` | Reopen closed ad → draft |

**Edit rules:**
- `draft`: all content fields editable (`title`, `description`, `requirements`, `skills`, `responsibilities`, `city`, `area`, `deadline`, `platforms`).
- `published`: only `deadline` and `platforms` editable.
- `closed`: no edits allowed — reopen first.
- `DELETE`: draft only. Close first if published.

**Status lifecycle:** `draft` → `published` → `closed` → `draft` (via reopen)

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
  "status": "draft",
  "published_at": null,
  "closed_at": null
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

---

### 7.1 New Recruitment Endpoints (v1.1)

All endpoints below are under `/api/v1/hris/recruitment/`.

---

#### Hiring Requests — New Actions

**Updated list filters** (`GET /hiring-requests/`):

| Query Param | Description |
|-------------|-------------|
| `?department=<id>` | Filter by department ID |
| `?status=` | Filter by status (`draft`, `submitted`, `approved`, `rejected`) |
| `?job_title=<id>` | Filter by job title ID |
| `?created_by=<id>` | Filter by creator user ID |

---

##### GET `/api/v1/hris/recruitment/hiring-requests/{id}/approval-flow/`
**Auth:** Bearer Token

Returns the full approval chain timeline for a hiring request.

**Response (200):**
```json
[
  {
    "id": 1,
    "role_type": "employee",
    "approver": 5,
    "approver_name": "Ahmed Mohamed",
    "status": "approved",
    "action_at": "2026-05-01T10:00:00Z",
    "note": "Looks good",
    "created_at": "2026-04-30T09:00:00Z"
  },
  {
    "id": 2,
    "role_type": "hr_employee",
    "approver": null,
    "approver_name": null,
    "status": "pending",
    "action_at": null,
    "note": null,
    "created_at": "2026-04-30T09:00:00Z"
  }
]
```

---

##### POST `/api/v1/hris/recruitment/hiring-requests/bulk-approve/`
**Auth:** Bearer Token

Bulk approve up to 100 hiring requests in one call.

**Request:**
```json
{ "ids": [1, 2], "role_type": "hr_employee", "note": "Approved in batch" }
```

**Response (200):**
```json
{ "success": [1, 2], "failed": [{"id": 3, "error": "Not in SUBMITTED status"}] }
```

---

##### POST `/api/v1/hris/recruitment/hiring-requests/bulk-reject/`
**Auth:** Bearer Token

**Request:**
```json
{ "ids": [3], "role_type": "hr_employee", "reason": "Budget freeze" }
```

**Response (200):** Same bulk response format — `success` and `failed` arrays.

---

##### POST `/api/v1/hris/recruitment/hiring-requests/bulk-delete/`
**Auth:** Bearer Token

Soft-deletes draft hiring requests in bulk.

**Request:**
```json
{ "ids": [4, 5] }
```

**Response (200):** Same bulk response format.

> **Bulk response format (all bulk endpoints):**
> ```json
> { "success": [1, 2], "failed": [{"id": 3, "error": "Not in DRAFT status"}] }
> ```
> Maximum 100 IDs per request.

---

#### Job Advertisements — New Actions

**Updated list filters** (`GET /job-advertisements/`):

| Query Param | Description |
|-------------|-------------|
| `?status=` | Filter by status (`draft`, `published`, `closed`) |
| `?city=` | Filter by city |
| `?area=` | Filter by area |
| `?platforms=` | Filter by platform |
| `?deadline_before=YYYY-MM-DD` | Ads with deadline before this date |
| `?deadline_after=YYYY-MM-DD` | Ads with deadline after this date |

---

##### POST `/api/v1/hris/recruitment/job-advertisements/bulk-publish/`
**Auth:** Bearer Token

**Request:**
```json
{ "ids": [1, 2] }
```

**Response (200):** Bulk response format.

---

##### POST `/api/v1/hris/recruitment/job-advertisements/bulk-close/`
**Auth:** Bearer Token

**Request:**
```json
{ "ids": [3] }
```

**Response (200):** Bulk response format.

---

#### Job Applications — New Actions

**Updated list filters** (`GET /applications/`):

| Query Param | Description |
|-------------|-------------|
| `?status=` | Filter by pipeline status |
| `?classification=` | Filter by classification (`shortlist_1`, `shortlist_2`, `none`) |
| `?job_board=` | Filter by source (`linkedin`, `facebook`, `bayt`, `recommendation`, `internal`, `other`) |
| `?job_advertisement=<id>` | Filter by job advertisement ID |
| `?candidate=<id>` | Filter by candidate ID |

---

##### POST `/api/v1/hris/recruitment/applications/import-cvs/`
**Auth:** Bearer Token | **Content-Type:** `multipart/form-data`

Import candidates from an Excel (.xlsx) or CSV file.

**Request (multipart form):**

| Field | Type | Description |
|-------|------|-------------|
| `file` | File | `.xlsx` or `.csv` (max 5 MB, 1000 rows) |
| `job_advertisement_id` | Integer | Target job advertisement |

**Response (200):**
```json
{
  "added": 45,
  "shortlist_1": 10,
  "shortlist_2": 5,
  "rejected": 3,
  "errors": [
    { "row": 12, "error": "Invalid email format" }
  ],
  "imported_at": "2026-05-01T10:00:00Z"
}
```

---

##### POST `/api/v1/hris/recruitment/applications/sync-from-job-boards/`
**Auth:** Bearer Token

Sync applications from external job boards (placeholder — returns mock data).

**Request:**
```json
{ "job_advertisement_id": 1, "platforms": ["linkedin", "bayt"] }
```

**Response (200):**
```json
{
  "synced": 12,
  "skipped_duplicates": 3,
  "platforms_attempted": ["linkedin", "bayt"],
  "synced_at": "2026-05-01T10:00:00Z"
}
```

---

##### POST `/api/v1/hris/recruitment/applications/bulk-edit/`
**Auth:** Bearer Token

Bulk update the classification on multiple applications.

**Request:**
```json
{ "ids": [1, 2, 3], "classification": "shortlist_1" }
```

**Response (200):** Bulk response format.

---

#### Audit Log — New Endpoints

All audit log endpoints are read-only and scoped to a specific recruitment entity type.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/hris/recruitment/audit-log/hiring-requests/` | Audit trail for hiring requests |
| GET | `/api/v1/hris/recruitment/audit-log/job-advertisements/` | Audit trail for job advertisements |
| GET | `/api/v1/hris/recruitment/audit-log/applications/` | Audit trail for applications |

**Query parameters (all three):**

| Param | Description |
|-------|-------------|
| `?action_type=` | Filter by action name (e.g. `submitted`, `approved`) |
| `?performed_by=<id>` | Filter by user ID |
| `?from_date=YYYY-MM-DD` | Start of date range |
| `?to_date=YYYY-MM-DD` | End of date range |
| `?search=` | Search within action name |

**Response (200) — paginated:**
```json
{
  "count": 50,
  "next": "...",
  "previous": null,
  "results": [
    {
      "id": 1,
      "action": "submitted",
      "entity_type": "hiring_request",
      "entity_id": 5,
      "performed_by_name": "Hassan Ashraf",
      "performed_by_id": 3,
      "timestamp": "2026-05-01T10:00:00Z",
      "details": {}
    }
  ]
}
```

---

#### Post-Probation Evaluation — New Resource

Full CRUD plus a multi-step approval workflow.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/hris/recruitment/post-probation/` | List / create |
| GET/PUT/PATCH/DELETE | `/api/v1/hris/recruitment/post-probation/{id}/` | Detail / update / delete |
| POST | `/api/v1/hris/recruitment/post-probation/{id}/submit-to-manager/` | Submit draft to manager |
| POST | `/api/v1/hris/recruitment/post-probation/{id}/manager-approve/` | Manager approves |
| POST | `/api/v1/hris/recruitment/post-probation/{id}/hr-confirm/` | HR confirms |
| POST | `/api/v1/hris/recruitment/post-probation/{id}/record-decision/` | Record final decision |

**Workflow status lifecycle:**
`draft` → `submitted_to_manager` → `manager_approved` → `hr_confirmed` → `final_decision`

**Create body:**
```json
{
  "application": 1,
  "evaluation_date": "2026-07-01",
  "tasks_score": 4,
  "attendance_score": 5,
  "initiative_score": 4,
  "collaboration_score": 3,
  "teamwork_score": 4
}
```

All score fields accept values 1–5. `average_score` is auto-computed on save.

**manager-approve body:**
```json
{ "note": "Good performance overall" }
```

**hr-confirm body:**
```json
{ "note": "Confirmed by HR" }
```

**record-decision body:**
```json
{ "decision": "confirmed", "rationale": "Excellent probation period" }
```

`decision` choices: `confirmed` | `terminated`

**Object:**
```json
{
  "id": 1,
  "application": 1,
  "evaluation_date": "2026-07-01",
  "tasks_score": 4,
  "attendance_score": 5,
  "initiative_score": 4,
  "collaboration_score": 3,
  "teamwork_score": 4,
  "average_score": 4.0,
  "performance_score": 0,
  "decision": "confirmed",
  "comments": null,
  "evaluated_by": 3,
  "evaluated_by_name": "Hassan Ashraf",
  "workflow_status": "draft",
  "manager_note": "",
  "hr_note": "",
  "rationale": "",
  "created_at": "2026-05-01T10:00:00Z",
  "updated_at": "2026-05-01T10:00:00Z"
}
```

---

#### Updated Object Schemas (v1.1)

##### JobApplication — new field

| Field | Type | Choices |
|-------|------|---------|
| `job_board` | string (nullable) | `linkedin`, `facebook`, `bayt`, `recommendation`, `internal`, `other` |

##### Interview — new field + updated `record-result`

| Field | Type | Choices |
|-------|------|---------|
| `call_status` | string (nullable) | `not_answered`, `suitable`, `call_back` |

`POST /interviews/{id}/record-result/` now accepts:
```json
{
  "scoring_data": [
    {"interviewer_id": 1, "score": 8.5, "note": "Strong communication"},
    {"interviewer_id": 2, "score": 7.0, "note": "Good technical skills"}
  ],
  "note": "Overall strong candidate",
  "call_status": "suitable"
}
```

`scoring_data` can be a list of per-interviewer scores (each `score` is 0–10). `average_score` is auto-computed.

##### JobOffer — new field

| Field | Type | Description |
|-------|------|-------------|
| `offer_validity_date` | date (nullable) | Offer expiry date — must be on or after `start_date` |

##### CandidateDocument — updated `doc_type`

Added `birth_certificate` to the `doc_type` choices:
`id_copy`, `qualification`, `military_status`, `personal_photo`, `police_clearance`, **`birth_certificate`**, `other`

##### Onboarding — new fields

| Field | Type | Description |
|-------|------|-------------|
| `session_date` | datetime (nullable) | Onboarding session date/time |
| `session_location` | string | Location of the session |
| `assigned_mentor` | FK (User, nullable) | Assigned mentor user |
| `attended` | boolean (nullable) | Whether the candidate attended |
| `engagement_level` | integer 1–5 (nullable) | Engagement rating |
| `survey_link` | URL (nullable) | Link to onboarding survey |
| `survey_responses` | JSON object | Structured survey responses |

---

### 8. Audit — `/api/v1/audit/`

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
| `internal_login` | 10 | per minute |
