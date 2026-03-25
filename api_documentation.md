# Ouvira API Documentation

**Base URL:** `http://localhost:8000` | **Content-Type:** `application/json`

**Headers required on all authenticated endpoints:**
```
Authorization: Bearer <access_token>
X-Tenant: <tenant_subdomain>
```

**Pagination** — all list endpoints return `{ "count", "next", "previous", "results" }` with 20 items per page. Use `?page=N`.

**Errors** — `{"detail": "..."}` or `{"field": ["error1"]}` with HTTP 400/401/403/404/429.

| Token | Lifetime |
|-------|----------|
| Access | 1 hour |
| Refresh | 7 days (rotated) |

---

# 1. Authentication — `api/auth/`

---

### POST `/api/auth/signup/`
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
{
  "message": "OTP sent successfully",
  "primary_mobile": "+201234567890"
}
```

---


### POST `/api/auth/finalize-signin/`
**Auth:** None | **Rate:** 3/hour

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

### POST `/api/auth/login/`
**Auth:** None | **Rate:** 5/min

> `identifier` accepts email or phone number.

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

### POST `/api/auth/token/refresh/`
**Auth:** None | **Rate:** 20/min

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

### POST `/api/auth/logout/`
**Auth:** Bearer Token

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

### POST `/api/auth/settings_enable-2fa/`
**Auth:** Bearer Token | **Rate:** 10/hour

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

### POST `/api/auth/login-2fa-verify-code/`
**Auth:** None | **Rate:** 5/min

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

### POST `/api/auth/login-2fa-verify-backup/`
**Auth:** None | **Rate:** 5/min

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

### POST `/api/auth/otp/send/`
**Auth:** None | **Rate:** 1/min
> Submits an OTP via email or SMS depending on the detected format of the `identifier`.

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

### POST `/api/auth/otp/verify/`
**Auth:** None | **Rate:** 5/min
> Validates the OTP securely (HMAC) and returns a success payload, advancing the user to login or finalized-signup.

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

### POST `/api/auth/password/forgot/`
**Auth:** None | **Rate:** 3/hour

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

### GET `/api/auth/password/validate-reset-token/`
**Auth:** None | **Rate:** Rate-limited at ingress

**Request Query Param:**
`?token=b4b2c1d3...`

**Response (200):**
```json
{
  "valid": true
}
```

---

### POST `/api/auth/password/reset/`
**Auth:** None | **Rate:** 3/hour (Shared with forgot)

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

### POST `/api/auth/password/change/`
**Auth:** Bearer Token | **Rate:** 10/hour

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

# 2. Account Management — `api/account/`

---

### GET `/api/account/profile/`
**Auth:** Bearer Token

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

### PUT/PATCH `/api/account/profile/`
**Auth:** Bearer Token

**Request:**
```json
{
  "full_name": "Hassan Ashraf",
  "email": "hassan-updated@example.com"
}
```

**Response (200):**
_Returns full user profile json block._

---

### GET `/api/account/users/`
**Auth:** Bearer + Admin
> Lists all active system users. Intended for administrative directory lookups. Optionally filter by `?company=<id>`.

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

# 3. Access Control — `api/access-control/`

---

### GET `/api/access-control/permissions/`
**Auth:** Bearer + Admin

**Response (200):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "code": "can_edit_company",
      "module": "company",
      "description": "Can edit company details",
      "created_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

---

### POST `/api/access-control/permissions/`
**Auth:** Bearer + Admin

**Request:**
```json
{
  "code": "can_create_invoice",
  "module": "billing",
  "description": "Can create new invoices"
}
```

**Response (201):**
```json
{
  "id": 3,
  "code": "can_create_invoice",
  "module": "billing",
  "description": "Can create new invoices",
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

---

### GET `/api/access-control/permissions/{id}/`
**Auth:** Bearer + Admin

**Response (200):**
```json
{
  "id": 1,
  "code": "can_edit_company",
  "module": "company",
  "description": "Can edit company details",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

---

### PUT `/api/access-control/permissions/{id}/`
**Auth:** Bearer + Admin

**Request:**
```json
{
  "code": "can_edit_company",
  "module": "company",
  "description": "Updated description here"
}
```

**Response (200):**
```json
{
  "id": 1,
  "code": "can_edit_company",
  "module": "company",
  "description": "Updated description here",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

---

### PATCH `/api/access-control/permissions/{id}/`
**Auth:** Bearer + Admin

**Request:**
```json
{
  "description": "Partial update description"
}
```

**Response (200):**
```json
{
  "id": 1,
  "code": "can_edit_company",
  "module": "company",
  "description": "Partial update description",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

---

### DELETE `/api/access-control/permissions/{id}/`
**Auth:** Bearer + Admin

**Response (204):** No content

---

### GET `/api/access-control/roles/`
**Auth:** Bearer + Admin

**Response (200):**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "role": "Editor",
      "desc": "Can edit content",
      "company": 1,
      "is_system_role": false,
      "created_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

---

### POST `/api/access-control/roles/`
**Auth:** Bearer + Admin

**Request:**
```json
{
  "role": "Viewer",
  "desc": "Read-only access",
  "company": 1
}
```

**Response (201):**
```json
{
  "id": 4,
  "role": "Viewer",
  "desc": "Read-only access",
  "company": 1,
  "is_system_role": false,
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

---

### GET `/api/access-control/roles/{id}/`
**Auth:** Bearer + Admin

**Response (200):**
```json
{
  "id": 1,
  "role": "Editor",
  "desc": "Can edit content",
  "company": 1,
  "is_system_role": false,
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

---

### PUT `/api/access-control/roles/{id}/`
**Auth:** Bearer + Admin

**Request:**
```json
{
  "role": "Editor",
  "desc": "Updated: can edit and publish content",
  "company": 1
}
```

**Response (200):**
```json
{
  "id": 1,
  "role": "Editor",
  "desc": "Updated: can edit and publish content",
  "company": 1,
  "is_system_role": false,
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

---

### PATCH `/api/access-control/roles/{id}/`
**Auth:** Bearer + Admin

**Request:**
```json
{
  "desc": "Partial update to role description"
}
```

**Response (200):**
```json
{
  "id": 1,
  "role": "Editor",
  "desc": "Partial update to role description",
  "company": 1,
  "is_system_role": false,
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

---

### DELETE `/api/access-control/roles/{id}/`
**Auth:** Bearer + Admin

**Response (204):** No content

---

### GET `/api/access-control/role-permissions/`
**Auth:** Bearer + Admin

**Response (200):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "role": 1,
      "permission": 2,
      "created_at": "2026-01-15T10:00:00Z",
      "updated_at": "2026-01-15T10:00:00Z",
      "deleted_at": null,
      "is_deleted": false
    }
  ]
}
```

---

### POST `/api/access-control/role-permissions/`
**Auth:** Bearer + Admin

**Request:**
```json
{
  "role": 1,
  "permission": 3
}
```

**Response (201):**
```json
{
  "id": 5,
  "role": 1,
  "permission": 3,
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

---

### GET `/api/access-control/role-permissions/{id}/`
**Auth:** Bearer + Admin

**Response (200):**
```json
{
  "id": 1,
  "role": 1,
  "permission": 2,
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

---

### DELETE `/api/access-control/role-permissions/{id}/`
**Auth:** Bearer + Admin

**Response (204):** No content

---

### GET `/api/access-control/user-companies/`
**Auth:** Bearer + Admin

**Response (200):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": 1,
      "company": 1,
      "is_active": true,
      "joined_at": "2026-01-15T10:00:00Z",
      "created_at": "2026-01-15T10:00:00Z",
      "updated_at": "2026-01-15T10:00:00Z",
      "deleted_at": null,
      "is_deleted": false
    }
  ]
}
```

---

### POST `/api/access-control/user-companies/`
**Auth:** Bearer + Admin

**Request:**
```json
{
  "user": 5,
  "company": 1
}
```

**Response (201):**
```json
{
  "id": 3,
  "user": 5,
  "company": 1,
  "is_active": true,
  "joined_at": "2026-02-17T10:00:00Z",
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

---

### GET `/api/access-control/user-companies/{id}/`
**Auth:** Bearer + Admin

**Response (200):**
```json
{
  "id": 1,
  "user": 1,
  "company": 1,
  "is_active": true,
  "joined_at": "2026-01-15T10:00:00Z",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

---

### PUT `/api/access-control/user-companies/{id}/`
**Auth:** Bearer + Admin

**Request:**
```json
{
  "user": 1,
  "company": 1,
  "is_active": false
}
```

**Response (200):**
```json
{
  "id": 1,
  "user": 1,
  "company": 1,
  "is_active": false,
  "joined_at": "2026-01-15T10:00:00Z",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

---

### DELETE `/api/access-control/user-companies/{id}/`
**Auth:** Bearer + Admin

**Response (204):** No content

---

### GET `/api/access-control/user-company-roles/`
**Auth:** Bearer + Admin

**Response (200):**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user_company": {
        "id": 1,
        "user": 1,
        "company": 1,
        "is_active": true
      },
      "role": {
        "id": 1,
        "role": "Editor",
        "desc": "Can edit content",
        "company": 1
      },
      "assigned_at": "2026-01-15T10:00:00Z",
      "created_at": "2026-01-15T10:00:00Z",
      "updated_at": "2026-01-15T10:00:00Z",
      "deleted_at": null,
      "is_deleted": false
    }
  ]
}
```

---

### POST `/api/access-control/user-company-roles/`
**Auth:** Bearer + Admin

**Request:**
```json
{
  "user_company": 1,
  "role": 2
}
```

**Response (201):**
```json
{
  "id": 2,
  "user_company": 1,
  "role": 2,
  "assigned_at": "2026-02-17T10:00:00Z",
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

---

### GET `/api/access-control/user-company-roles/{id}/`
**Auth:** Bearer + Admin

**Response (200):**
```json
{
  "id": 1,
  "user_company": {
    "id": 1,
    "user": 1,
    "company": 1,
    "is_active": true
  },
  "role": {
    "id": 1,
    "role": "Editor",
    "desc": "Can edit content",
    "company": 1
  },
  "assigned_at": "2026-01-15T10:00:00Z",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z",
  "deleted_at": null,
  "is_deleted": false
}
```

---

### DELETE `/api/access-control/user-company-roles/{id}/`
**Auth:** Bearer + Admin

**Response (204):** No content

---

### GET `/api/access-control/invitations/`
**Auth:** Bearer + Admin | **Query Params:** `?company=1&status=pending`

**Response (200):**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "email": "newuser@example.com",
      "company": 1,
      "role": 2,
      "status": "pending",
      "expires_at": "2026-03-01T00:00:00Z",
      "created_at": "2026-02-17T10:00:00Z"
    }
  ]
}
```

---

### POST `/api/access-control/invitations/`
**Auth:** Bearer + Admin

**Request:**
```json
{
  "email": "newuser@example.com",
  "company": 1,
  "role": 2,
  "expires_at": "2026-03-01T00:00:00Z"
}
```

**Response (201):**
```json
{
  "id": 2,
  "email": "newuser@example.com",
  "company": 1,
  "role": 2,
  "token": "auto-generated-token",
  "status": "pending",
  "expires_at": "2026-03-01T00:00:00Z",
  "invited_by": 1,
  "accepted_by": null,
  "created_at": "2026-02-17T10:00:00Z"
}
```

---

### GET `/api/access-control/invitations/{id}/`
**Auth:** Bearer + Admin

**Response (200):**
```json
{
  "id": 1,
  "email": "newuser@example.com",
  "company": 1,
  "role": 2,
  "token": "invitation-token",
  "status": "pending",
  "expires_at": "2026-03-01T00:00:00Z",
  "invited_by": 1,
  "accepted_by": null,
  "created_at": "2026-02-17T10:00:00Z"
}
```

---

### PUT `/api/access-control/invitations/{id}/`
**Auth:** Bearer + Admin

**Request:**
```json
{
  "email": "newuser@example.com",
  "company": 1,
  "role": 3,
  "expires_at": "2026-04-01T00:00:00Z"
}
```

**Response (200):**
```json
{
  "id": 1,
  "email": "newuser@example.com",
  "company": 1,
  "role": 3,
  "token": "invitation-token",
  "status": "pending",
  "expires_at": "2026-04-01T00:00:00Z",
  "invited_by": 1,
  "accepted_by": null,
  "created_at": "2026-02-17T10:00:00Z"
}
```

---

### DELETE `/api/access-control/invitations/{id}/`
**Auth:** Bearer + Admin

**Response (204):** No content

---

### POST `/api/access-control/invitations/accept/`
**Auth:** Bearer Token

**Request:**
```json
{
  "token": "invitation-token-string"
}
```

**Response (200):**
```json
{
  "detail": "Invitation accepted successfully."
}
```

---

### POST `/api/access-control/invitations/{id}/revoke/`
**Auth:** Bearer + Admin

**Request:** *(empty body)*

**Response (200):**
```json
{
  "detail": "Invitation revoked."
}
```

---

### POST `/api/access-control/invitations/{id}/resend/`
**Auth:** Bearer + Admin

**Request:** *(empty body)*

**Response (200):**
```json
{
  "detail": "Invitation resent."
}
```

---

# 3. Company — `api/company/`

---

### GET `/api/company/`
**Auth:** Bearer Token

**Response (200):**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Ouvira Inc.",
      "logo": null,
      "status": "active",
      "is_parent_company": true,
      "created_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

---

### POST `/api/company/`
**Auth:** Bearer Token

**Request:**
```json
{
  "name": "Ouvira Inc.",
  "description": "A technology company",
  "address": "Cairo, Egypt",
  "parent_company": null,
  "is_parent_company": true
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "Ouvira Inc.",
  "logo": null,
  "create_by": 1,
  "parent_company": null,
  "is_parent_company": true,
  "description": "A technology company",
  "address": "Cairo, Egypt",
  "status": "active",
  "settings": {
    "id": 1,
    "default_language": "",
    "default_currency": "",
    "timezone": "",
    "fiscal_year_start_month": 1,
    "feature_flags": {}
  },
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z"
}
```

---

### GET `/api/company/{id}/`
**Auth:** Bearer Token

**Response (200):**
```json
{
  "id": 1,
  "name": "Ouvira Inc.",
  "logo": null,
  "create_by": 1,
  "parent_company": null,
  "is_parent_company": true,
  "description": "A technology company",
  "address": "Cairo, Egypt",
  "status": "active",
  "settings": {
    "id": 1,
    "default_language": "en",
    "default_currency": "EGP",
    "timezone": "Africa/Cairo",
    "fiscal_year_start_month": 1,
    "feature_flags": {}
  },
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z"
}
```

---

### PUT `/api/company/{id}/`
**Auth:** Bearer + Admin/Owner

> Status transitions: `active` → `deactivated`, `deactivated` → `active` or `deleted`

**Request:**
```json
{
  "name": "Ouvira Inc.",
  "description": "Updated description",
  "address": "New Cairo, Egypt",
  "parent_company": null,
  "is_parent_company": true,
  "status": "active"
}
```

**Response (200):**
```json
{
  "id": 1,
  "name": "Ouvira Inc.",
  "logo": null,
  "create_by": 1,
  "parent_company": null,
  "is_parent_company": true,
  "description": "Updated description",
  "address": "New Cairo, Egypt",
  "status": "active",
  "settings": { "..." : "..." },
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-02-17T12:00:00Z"
}
```

---

### PATCH `/api/company/{id}/`
**Auth:** Bearer + Admin/Owner

**Request:**
```json
{
  "description": "Partially updated description"
}
```

**Response (200):**
```json
{
  "id": 1,
  "name": "Ouvira Inc.",
  "logo": null,
  "create_by": 1,
  "parent_company": null,
  "is_parent_company": true,
  "description": "Partially updated description",
  "address": "Cairo, Egypt",
  "status": "active",
  "settings": { "..." : "..." },
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-02-17T12:00:00Z"
}
```

---

### DELETE `/api/company/{id}/`
**Auth:** Bearer + Owner only (soft delete)

**Response (204):** No content

---

### GET `/api/company/{id}/settings/`
**Auth:** Bearer Token

**Response (200):**
```json
{
  "id": 1,
  "company": 1,
  "default_language": "en",
  "default_currency": "EGP",
  "timezone": "Africa/Cairo",
  "fiscal_year_start_month": 1,
  "feature_flags": {},
  "updated_at": "2026-02-17T10:00:00Z"
}
```

---

### PUT `/api/company/{id}/settings/`
**Auth:** Bearer + Admin/Owner

**Request:**
```json
{
  "default_language": "ar",
  "default_currency": "EGP",
  "timezone": "Africa/Cairo",
  "fiscal_year_start_month": 7,
  "feature_flags": {
    "dark_mode": true,
    "beta_features": false
  }
}
```

**Response (200):**
```json
{
  "id": 1,
  "company": 1,
  "default_language": "ar",
  "default_currency": "EGP",
  "timezone": "Africa/Cairo",
  "fiscal_year_start_month": 7,
  "feature_flags": {
    "dark_mode": true,
    "beta_features": false
  },
  "updated_at": "2026-02-17T12:00:00Z"
}
```

---

### PATCH `/api/company/{id}/settings/`
**Auth:** Bearer + Admin/Owner

**Request:**
```json
{
  "default_language": "fr"
}
```

**Response (200):**
```json
{
  "id": 1,
  "company": 1,
  "default_language": "fr",
  "default_currency": "EGP",
  "timezone": "Africa/Cairo",
  "fiscal_year_start_month": 7,
  "feature_flags": {
    "dark_mode": true,
    "beta_features": false
  },
  "updated_at": "2026-02-17T13:00:00Z"
}
```

---

# 4. Account — `api/account/`

---

### GET `/api/account/profile/`
**Auth:** Bearer Token

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
  "account_uid": "uuid-here",
  "is_2fa_enabled": false,
  "two_fa_type": null,
  "date_joined": "2026-01-15T10:00:00Z",
  "last_login": "2026-02-17T10:00:00Z"
}
```

---

### PUT `/api/account/profile/`
**Auth:** Bearer Token

**Request:**
```json
{
  "full_name": "Hassan Ahmed Ashraf",
  "email": "newemail@example.com"
}
```

**Response (200):**
```json
{
  "full_name": "Hassan Ahmed Ashraf",
  "email": "newemail@example.com"
}
```

---

### PATCH `/api/account/profile/`
**Auth:** Bearer Token

**Request:**
```json
{
  "full_name": "Hassan A. Ashraf"
}
```

**Response (200):**
```json
{
  "full_name": "Hassan A. Ashraf",
  "email": "newemail@example.com"
}
```

---

### GET `/api/account/users/`
**Auth:** Bearer + Admin | **Query Params:** `?company=1`

**Response (200):**
```json
{
  "count": 5,
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

### GET `/api/account/session-tests/`
**Auth:** Bearer Token

**Response (200):**
```json
{
  "user": "hassan",
  "token_expires_at": "2026-02-17T11:00:00Z"
}
```

---

# 5. Audit — `api/audit/`

---

### GET `/api/audit/notifications/`
**Auth:** Bearer Token | **Query Params:** `?unread=true`

**Response (200):**
```json
{
  "unread_count": 3,
  "results": [
    {
      "id": 1,
      "message": "Welcome! You have successfully registered.",
      "read": false,
      "created_at": "2026-01-15T10:00:00Z"
    },
    {
      "id": 2,
      "message": "Your company settings were updated.",
      "read": true,
      "created_at": "2026-02-10T08:00:00Z"
    }
  ]
}
```

---

### POST `/api/audit/notifications/mark-read/` — Mark Single
**Auth:** Bearer Token

**Request:**
```json
{
  "notification_id": 1
}
```

**Response (200):**
```json
{
  "detail": "Notification marked as read."
}
```

---

### POST `/api/audit/notifications/mark-read/` — Mark All
**Auth:** Bearer Token

**Request:**
```json
{
  "all": true
}
```

**Response (200):**
```json
{
  "detail": "Marked 3 notifications as read."
}
```

---

### GET `/api/audit/activity-logs/`
**Auth:** Bearer + Admin | **Query Params:** `?company=1`

**Response (200):**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user_display": "hassan",
      "entity_type": "Company",
      "action": "UPDATE",
      "created_at": "2026-02-17T10:00:00Z"
    }
  ]
}
```

---

### GET `/api/audit/activity-logs/my/`
**Auth:** Bearer Token

**Response (200):**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": 1,
      "user_display": "hassan",
      "company": 1,
      "date": 20260217,
      "entity_type": "Company",
      "entity_id": 1,
      "action": "UPDATE",
      "old_values": { "name": "Old Name" },
      "new_values": { "name": "New Name" },
      "ip_address": "192.168.1.1",
      "created_at": "2026-02-17T10:00:00Z"
    }
  ]
}
```

---

### GET `/api/audit/security-logs/`
**Auth:** Bearer Token

**Response (200):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": 1,
      "user_display": "hassan",
      "date": 20260217,
      "action": "LOGIN_SUCCESS",
      "metadata": {
        "device": "Chrome on Windows",
        "ip": "192.168.1.1"
      },
      "ip_address": "192.168.1.1",
      "created_at": "2026-02-17T10:00:00Z"
    }
  ]
}
```

---

# Quick Reference

| Module | Method | Endpoint | Auth |
|--------|--------|----------|------|
| Auth | POST | `/api/auth/signup/` | None |
| Auth | POST | `/api/auth/verify-otp/` | None |
| Auth | POST | `/api/auth/resent-otp/` | None |
| Auth | POST | `/api/auth/finalize-signin/` | None |
| Auth | POST | `/api/auth/login/` | None |
| Auth | POST | `/api/auth/logout/` | Bearer |
| Auth | POST | `/api/auth/token/refresh/` | None |
| Auth | POST | `/api/auth/settings_enable-2fa/` | Bearer |
| Auth | POST | `/api/auth/login-2fa-verify-code/` | None |
| Auth | POST | `/api/auth/login-2fa-verify-backup/` | None |
| Access | GET | `/api/access-control/permissions/` | Admin |
| Access | POST | `/api/access-control/permissions/` | Admin |
| Access | GET | `/api/access-control/permissions/{id}/` | Admin |
| Access | PUT | `/api/access-control/permissions/{id}/` | Admin |
| Access | PATCH | `/api/access-control/permissions/{id}/` | Admin |
| Access | DELETE | `/api/access-control/permissions/{id}/` | Admin |
| Access | GET | `/api/access-control/roles/` | Admin |
| Access | POST | `/api/access-control/roles/` | Admin |
| Access | GET | `/api/access-control/roles/{id}/` | Admin |
| Access | PUT | `/api/access-control/roles/{id}/` | Admin |
| Access | PATCH | `/api/access-control/roles/{id}/` | Admin |
| Access | DELETE | `/api/access-control/roles/{id}/` | Admin |
| Access | GET | `/api/access-control/role-permissions/` | Admin |
| Access | POST | `/api/access-control/role-permissions/` | Admin |
| Access | GET | `/api/access-control/role-permissions/{id}/` | Admin |
| Access | DELETE | `/api/access-control/role-permissions/{id}/` | Admin |
| Access | GET | `/api/access-control/user-companies/` | Admin |
| Access | POST | `/api/access-control/user-companies/` | Admin |
| Access | GET | `/api/access-control/user-companies/{id}/` | Admin |
| Access | PUT | `/api/access-control/user-companies/{id}/` | Admin |
| Access | DELETE | `/api/access-control/user-companies/{id}/` | Admin |
| Access | GET | `/api/access-control/user-company-roles/` | Admin |
| Access | POST | `/api/access-control/user-company-roles/` | Admin |
| Access | GET | `/api/access-control/user-company-roles/{id}/` | Admin |
| Access | DELETE | `/api/access-control/user-company-roles/{id}/` | Admin |
| Access | GET | `/api/access-control/invitations/` | Admin |
| Access | POST | `/api/access-control/invitations/` | Admin |
| Access | GET | `/api/access-control/invitations/{id}/` | Admin |
| Access | PUT | `/api/access-control/invitations/{id}/` | Admin |
| Access | DELETE | `/api/access-control/invitations/{id}/` | Admin |
| Access | POST | `/api/access-control/invitations/accept/` | Bearer |
| Access | POST | `/api/access-control/invitations/{id}/revoke/` | Admin |
| Access | POST | `/api/access-control/invitations/{id}/resend/` | Admin |
| Company | GET | `/api/company/` | Bearer |
| Company | POST | `/api/company/` | Bearer |
| Company | GET | `/api/company/{id}/` | Bearer |
| Company | PUT | `/api/company/{id}/` | Admin/Owner |
| Company | PATCH | `/api/company/{id}/` | Admin/Owner |
| Company | DELETE | `/api/company/{id}/` | Owner |
| Company | GET | `/api/company/{id}/settings/` | Bearer |
| Company | PUT | `/api/company/{id}/settings/` | Admin/Owner |
| Company | PATCH | `/api/company/{id}/settings/` | Admin/Owner |
| Account | GET | `/api/account/profile/` | Bearer |
| Account | PUT | `/api/account/profile/` | Bearer |
| Account | PATCH | `/api/account/profile/` | Bearer |
| Account | GET | `/api/account/users/` | Admin |
| Account | GET | `/api/account/session-tests/` | Bearer |
| Audit | GET | `/api/audit/notifications/` | Bearer |
| Audit | POST | `/api/audit/notifications/mark-read/` | Bearer |
| Audit | GET | `/api/audit/activity-logs/` | Admin |
| Audit | GET | `/api/audit/activity-logs/my/` | Bearer |
| Audit | GET | `/api/audit/security-logs/` | Bearer |

---

## Rate Limits

| Scope | Limit |
|-------|-------|
| Anonymous | 200/day |
| Authenticated | 1000/day |
| Signup | 3/hour |
| Finalize Signin | 3/hour |
| Login | 5/min |
| OTP Resend | 3/hour |
| OTP Verify | 5/min |
| 2FA Verify | 5/min |
| Token Refresh | 20/min |
| Enable 2FA | 10/hour |

---

## Interactive Docs

| Tool | URL |
|------|-----|
| Swagger UI | `/swagger/` |
| ReDoc | `/redoc/` |
| OpenAPI JSON | `/swagger.json` |
| OpenAPI YAML | `/swagger.yaml` |
