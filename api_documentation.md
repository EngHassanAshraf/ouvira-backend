# Ouvira API Documentation

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000` (development) | `https://api.ouvira.com` (production)  
**Content-Type:** `application/json`

---

## 📋 Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [Endpoints](#endpoints)
   - [Authentication](#1-authentication---apiauth)
   - [Account Management](#2-account-management---apiaccount)
   - [Access Control](#3-access-control---apiaccess-control)
   - [Company](#4-company---apicompany)
   - [Audit](#5-audit---apiaudit)
   - [HRIS Core](#6-hris-core---apihris)
   - [Recruitment](#7-recruitment---apihrisrecruitment)
5. [Pagination](#pagination)
6. [Rate Limiting](#rate-limiting)

---

## API Overview

### Versioning
The API uses URL-based versioning. All endpoints are prefixed with `/api/`.

### Required Headers

All authenticated endpoints require:
```
Authorization: Bearer <access_token>
X-Tenant: <tenant_subdomain>
```

### Response Format

**Success Response:**
```json
{
  "id": 1,
  "field": "value",
  "created_at": "2026-01-15T10:00:00Z"
}
```

**List Response:**
```json
{
  "count": 100,
  "next": "http://api.ouvira.com/endpoint?page=2",
  "previous": null,
  "results": [...]
}
```

**Error Response:**
```json
{
  "detail": "Error message here"
}
```

or

```json
{
  "field_name": ["Error message for this field"]
}
```

---

## Authentication

### Token Lifecycle

| Token Type | Lifetime | Usage |
|------------|----------|-------|
| Access Token | 1 hour | API authentication |
| Refresh Token | 7 days | Obtain new access token |

### Obtaining Tokens

1. **Signup Flow:**
   - `POST /api/auth/signup/` → OTP sent
   - `POST /api/auth/finalize-signin/` → Tokens returned

2. **Login Flow:**
   - `POST /api/auth/login/` → Tokens returned (or 2FA required)
   - If 2FA enabled: `POST /api/auth/login-2fa-verify-code/` → Tokens returned

### Using Tokens

Include in all authenticated requests:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Error Response Format

```json
{
  "detail": "Human-readable error message"
}
```

For validation errors:
```json
{
  "email": ["Enter a valid email address."],
  "password": ["This field is required."]
}
```

---

## Endpoints

### 1. Authentication — `/api/auth/`

#### POST `/api/auth/signup/`
**Auth:** None | **Rate:** 3/hour

Start the signup process by sending an OTP.

**Request:**
```json
{
  "full_name": "Hassan Ashraf",
  "primary_mobile": "+201234567890"
}
```

**Response (201):**
```json
{
  "message": "OTP sent successfully",
  "primary_mobile": "+201234567890"
}
```

---

#### POST `/api/auth/finalize-signin/`
**Auth:** None | **Rate:** 3/hour

Complete signup after OTP verification.

**Request:**
```json
{
  "primary_mobile": "+201234567890",
  "email": "hassan@example.com",
  "password": "SecureP@ss123"
}
```

**Response (201):**
```json
{
  "message": "Account created successfully",
  "tokens": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  }
}
```

---

#### POST `/api/auth/login/`
**Auth:** None | **Rate:** 5/min

Login with email or phone number.

**Request:**
```json
{
  "identifier": "hassan@example.com",
  "password": "SecureP@ss123"
}
```

**Response (200) — without 2FA:**
```json
{
  "tokens": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  },
  "user": {
    "id": 1,
    "username": "hassan",
    "full_name": "Hassan Ashraf",
    "email": "hassan@example.com"
  }
}
```

**Response (200) — with 2FA enabled:**
```json
{
  "requires_2fa": true,
  "session_id": "uuid-session-id"
}
```

---

#### POST `/api/auth/token/refresh/`
**Auth:** None | **Rate:** 20/min

Refresh access token using refresh token.

**Request:**
```json
{
  "refresh": "eyJ..."
}
```

**Response (200):**
```json
{
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

---

#### POST `/api/auth/logout/`
**Auth:** Bearer Token

Logout and blacklist the refresh token.

**Request:**
```json
{
  "refresh": "eyJ..."
}
```

**Response (205):**
```json
{
  "detail": "Successfully logged out."
}
```

---

#### POST `/api/auth/settings_enable-2fa/`
**Auth:** Bearer Token | **Rate:** 10/hour

Enable two-factor authentication.

**Request:**
```json
{
  "method": "totp"
}
```

**Response (200):**
```json
{
  "secret": "BASE32SECRET",
  "qr_code": "otpauth://totp/Ouvira:hassan@example.com?secret=BASE32SECRET&issuer=Ouvira",
  "backup_codes": ["code1", "code2", "code3", "code4", "code5"]
}
```

---

#### POST `/api/auth/login-2fa-verify-code/`
**Auth:** None | **Rate:** 5/min

Verify 2FA code during login.

**Request:**
```json
{
  "session_id": "uuid-session-id",
  "code": "123456"
}
```

**Response (200):**
```json
{
  "tokens": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  }
}
```

---

#### POST `/api/auth/login-2fa-verify-backup/`
**Auth:** None | **Rate:** 5/min

Verify backup code during login.

**Request:**
```json
{
  "session_id": "uuid-session-id",
  "backup_code": "backup-code-here"
}
```

**Response (200):**
```json
{
  "tokens": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  }
}
```

---

#### POST `/api/auth/otp/send/`
**Auth:** None | **Rate:** 1/min

Send OTP via email or SMS.

**Request:**
```json
{
  "identifier": "hassan@example.com"
}
```

**Response (200):**
```json
{
  "message": "OTP sent successfully"
}
```

---

#### POST `/api/auth/otp/verify/`
**Auth:** None | **Rate:** 5/min

Verify OTP.

**Request:**
```json
{
  "identifier": "hassan@example.com",
  "otp": "123456"
}
```

**Response (200):**
```json
{
  "message": "OTP verified successfully"
}
```

---

#### POST `/api/auth/password/forgot/`
**Auth:** None | **Rate:** 3/hour

Request password reset.

**Request:**
```json
{
  "identifier": "hassan@example.com"
}
```

**Response (200):**
```json
{
  "message": "If an account with that identifier exists, a password reset link has been sent."
}
```

---

#### GET `/api/auth/password/validate-reset-token/`
**Auth:** None

Validate password reset token.

**Query Params:** `?token=b4b2c1d3...`

**Response (200):**
```json
{
  "valid": true
}
```

---

#### POST `/api/auth/password/reset/`
**Auth:** None | **Rate:** 3/hour

Reset password with token.

**Request:**
```json
{
  "token": "b4b2c1d3...",
  "new_password": "NewSecurePassword123!"
}
```

**Response (200):**
```json
{
  "message": "Password reset successfully"
}
```

---

#### POST `/api/auth/password/change/`
**Auth:** Bearer Token | **Rate:** 10/hour

Change password (when current password is known).

**Request:**
```json
{
  "old_password": "CurrentSecurePassword123!",
  "new_password": "NewSecurePassword123!"
}
```

**Response (200):**
```json
{
  "message": "Password updated successfully"
}
```

---

### 2. Account Management — `/api/account/`

#### GET `/api/account/profile/`
**Auth:** Bearer Token

Get current user profile.

**Response (200):**
```json
{
  "id": 1,
  "username": "hassan",
  "full_name": "Hassan Ashraf",
  "email": "hassan@example.com",
  "primary_mobile": "+201234567890",
  "email_verified": true,
  "phone_verified": true,
  "account_uid": "USR-1234ABCD",
  "is_2fa_enabled": false,
  "two_fa_type": "AUTHENTICATOR",
  "date_joined": "2026-01-15T10:00:00Z",
  "last_login": "2026-03-24T22:00:00Z"
}
```

---

#### PUT/PATCH `/api/account/profile/`
**Auth:** Bearer Token

Update user profile.

**Request:**
```json
{
  "full_name": "Hassan Ashraf",
  "email": "hassan-updated@example.com"
}
```

**Response (200):** Returns full user profile.

---

#### GET `/api/account/users/`
**Auth:** Bearer + Admin

List all active system users.

**Query Params:** `?company=<id>`

**Response (200):**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "username": "hassan",
      "full_name": "Hassan Ashraf",
      "email": "hassan@example.com",
      "primary_mobile": "+201234567890",
      "is_active": true,
      "date_joined": "2026-01-15T10:00:00Z"
    }
  ]
}
```

---

### 3. Access Control — `/api/access-control/`

#### Permissions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/access-control/permissions/` | List all permissions |
| POST | `/api/access-control/permissions/` | Create permission |
| GET | `/api/access-control/permissions/{id}/` | Get permission details |
| PUT | `/api/access-control/permissions/{id}/` | Update permission |
| PATCH | `/api/access-control/permissions/{id}/` | Partial update |
| DELETE | `/api/access-control/permissions/{id}/` | Delete permission |

**Permission Object:**
```json
{
  "id": 1,
  "code": "can_edit_company",
  "module": "company",
  "description": "Can edit company details",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z"
}
```

---

#### Roles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/access-control/roles/` | List all roles |
| POST | `/api/access-control/roles/` | Create role |
| GET | `/api/access-control/roles/{id}/` | Get role details |
| PUT | `/api/access-control/roles/{id}/` | Update role |
| PATCH | `/api/access-control/roles/{id}/` | Partial update |
| DELETE | `/api/access-control/roles/{id}/` | Delete role |

**Role Object:**
```json
{
  "id": 1,
  "role": "Editor",
  "desc": "Can edit content",
  "company": 1,
  "is_system_role": false,
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z"
}
```

---

#### Role Permissions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/access-control/role-permissions/` | List role permissions |
| POST | `/api/access-control/role-permissions/` | Assign permission to role |
| DELETE | `/api/access-control/role-permissions/{id}/` | Remove permission from role |

---

#### User Companies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/access-control/user-companies/` | List user-company associations |
| POST | `/api/access-control/user-companies/` | Associate user with company |
| GET | `/api/access-control/user-companies/{id}/` | Get association details |
| PUT | `/api/access-control/user-companies/{id}/` | Update association |
| DELETE | `/api/access-control/user-companies/{id}/` | Remove association |

---

#### User Company Roles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/access-control/user-company-roles/` | List user roles in companies |
| POST | `/api/access-control/user-company-roles/` | Assign role to user in company |
| DELETE | `/api/access-control/user-company-roles/{id}/` | Remove role from user |

---

#### Invitations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/access-control/invitations/` | List invitations |
| POST | `/api/access-control/invitations/` | Create invitation |
| GET | `/api/access-control/invitations/{id}/` | Get invitation details |
| PUT | `/api/access-control/invitations/{id}/` | Update invitation |
| DELETE | `/api/access-control/invitations/{id}/` | Revoke invitation |
| POST | `/api/access-control/invitations/accept/` | Accept invitation |
| POST | `/api/access-control/invitations/{id}/resend/` | Resend invitation |

**Invitation Object:**
```json
{
  "id": 1,
  "email": "newuser@example.com",
  "company": 1,
  "role": 2,
  "status": "pending",
  "expires_at": "2026-03-01T00:00:00Z",
  "created_at": "2026-02-17T10:00:00Z"
}
```

---

### 4. Company — `/api/company/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/company/` | List companies |
| POST | `/api/company/` | Create company |
| GET | `/api/company/{id}/` | Get company details |
| PUT | `/api/company/{id}/` | Update company |
| PATCH | `/api/company/{id}/` | Partial update |
| DELETE | `/api/company/{id}/` | Delete company (owner only) |
| GET | `/api/company/{id}/settings/` | Get company settings |
| PUT | `/api/company/{id}/settings/` | Update company settings |

---

### 5. Audit — `/api/audit/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audit/notifications/` | List notifications |
| POST | `/api/audit/notifications/mark-read/` | Mark notifications as read |
| GET | `/api/audit/activity-logs/` | List activity logs (admin) |
| GET | `/api/audit/activity-logs/my/` | List my activity logs |
| GET | `/api/audit/security-logs/` | List security logs |

---

### 6. HRIS Core — `/api/hris/`

#### Employees

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/hris/employees/` | List employees |
| POST | `/api/hris/employees/` | Create employee |
| GET | `/api/hris/employees/{id}/` | Get employee details |
| PUT | `/api/hris/employees/{id}/` | Update employee |
| PATCH | `/api/hris/employees/{id}/` | Partial update |
| DELETE | `/api/hris/employees/{id}/` | Soft delete employee |

**Employee Object:**
```json
{
  "id": 1,
  "employee_id": "EMP-001",
  "first_name": "Ahmed",
  "last_name": "Mohamed",
  "national_id": "1234567890",
  "passport_number": "A12345678",
  "nationality": "Saudi Arabian",
  "date_of_birth": "1990-01-15",
  "gender": "M",
  "marital_status": "M",
  "contact_number": "+966501234567",
  "personal_email": "ahmed@example.com",
  "company": 1,
  "user": 1,
  "location": 1,
  "department": 1,
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z"
}
```

---

#### Departments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/hris/departments/` | List departments |
| POST | `/api/hris/departments/` | Create department |
| GET | `/api/hris/departments/{id}/` | Get department details |
| PUT | `/api/hris/departments/{id}/` | Update department |
| PATCH | `/api/hris/departments/{id}/` | Partial update |
| DELETE | `/api/hris/departments/{id}/` | Soft delete department |

---

#### Positions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/hris/positions/` | List positions |
| POST | `/api/hris/positions/` | Create position |
| GET | `/api/hris/positions/{id}/` | Get position details |
| PUT | `/api/hris/positions/{id}/` | Update position |
| PATCH | `/api/hris/positions/{id}/` | Partial update |
| DELETE | `/api/hris/positions/{id}/` | Soft delete position |

---

#### Locations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/hris/locations/` | List locations |
| POST | `/api/hris/locations/` | Create location |
| GET | `/api/hris/locations/{id}/` | Get location details |
| PUT | `/api/hris/locations/{id}/` | Update location |
| PATCH | `/api/hris/locations/{id}/` | Partial update |
| DELETE | `/api/hris/locations/{id}/` | Soft delete location |

---

#### Attendance

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/hris/attendance/` | List attendance records |
| POST | `/api/hris/attendance/` | Create attendance record |
| GET | `/api/hris/attendance/{id}/` | Get attendance details |
| PUT | `/api/hris/attendance/{id}/` | Update attendance record |
| PATCH | `/api/hris/attendance/{id}/` | Partial update |
| DELETE | `/api/hris/attendance/{id}/` | Soft delete attendance record |

---

### 7. Recruitment — `/api/hris/recruitment/`

#### Hiring Requests

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/hris/recruitment/hiring-requests/` | List hiring requests |
| POST | `/api/hris/recruitment/hiring-requests/` | Create hiring request |
| GET | `/api/hris/recruitment/hiring-requests/{id}/` | Get hiring request details |
| PUT | `/api/hris/recruitment/hiring-requests/{id}/` | Update hiring request |
| PATCH | `/api/hris/recruitment/hiring-requests/{id}/` | Partial update |
| DELETE | `/api/hris/recruitment/hiring-requests/{id}/` | Soft delete hiring request |

---

#### Candidates

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/hris/recruitment/candidates/` | List candidates |
| POST | `/api/hris/recruitment/candidates/` | Create candidate |
| GET | `/api/hris/recruitment/candidates/{id}/` | Get candidate details |
| PUT | `/api/hris/recruitment/candidates/{id}/` | Update candidate |
| PATCH | `/api/hris/recruitment/candidates/{id}/` | Partial update |
| DELETE | `/api/hris/recruitment/candidates/{id}/` | Soft delete candidate |

---

#### Job Applications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/hris/recruitment/applications/` | List job applications |
| POST | `/api/hris/recruitment/applications/` | Create job application |
| GET | `/api/hris/recruitment/applications/{id}/` | Get application details |
| PUT | `/api/hris/recruitment/applications/{id}/` | Update application |
| PATCH | `/api/hris/recruitment/applications/{id}/` | Partial update |
| DELETE | `/api/hris/recruitment/applications/{id}/` | Soft delete application |

---

#### Interviews

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/hris/recruitment/interviews/` | List interviews |
| POST | `/api/hris/recruitment/interviews/` | Create interview |
| GET | `/api/hris/recruitment/interviews/{id}/` | Get interview details |
| PUT | `/api/hris/recruitment/interviews/{id}/` | Update interview |
| PATCH | `/api/hris/recruitment/interviews/{id}/` | Partial update |
| DELETE | `/api/hris/recruitment/interviews/{id}/` | Soft delete interview |

---

## Pagination

All list endpoints support pagination with the following response format:

```json
{
  "count": 100,
  "next": "http://api.ouvira.com/endpoint?page=2",
  "previous": null,
  "results": [...]
}
```

**Query Parameters:**
- `page` — Page number (default: 1)
- `page_size` — Items per page (default: 20, max: 100)

**Example:**
```
GET /api/hris/employees/?page=2&page_size=50
```

---

## Rate Limiting

| Scope | Limit | Window |
|-------|-------|--------|
| Anonymous | 200 | per day |
| Authenticated | 1000 | per day |
| Login | 5 | per minute |
| OTP Verify | 5 | per minute |
| 2FA Verify | 5 | per minute |
| OTP Send | 1 | per minute |
| Token Refresh | 20 | per minute |
| Password Forgot | 3 | per hour |
| Password Change | 10 | per hour |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1647360000
```

---

## Security Considerations

1. **Always use HTTPS in production**
2. **Never share your SECRET_KEY or database credentials**
3. **Rotate API tokens regularly**
4. **Implement proper CORS settings for your frontend domain**
5. **Use the X-Tenant header to route requests to the correct tenant**
6. **Enable 2FA for all admin accounts**

---

## Support

For API support:
- **Swagger UI**: `/swagger/`
- **ReDoc**: `/redoc/`
- **GitHub Issues**: [Report issues](https://github.com/EngHassanAshraf/ouvira-backend/issues)