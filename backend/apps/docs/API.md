# 📌 POST /api/signup/

The user creates a new account and an `OTP` is sent to the phone number.
Through this endpoint:

- Create a new user or retrieve an existing user with a phone number and `full name`
- A new OTP will be generated and will be valid for `5 minutes`

---

### 📝 Request Body
```json
    {
      "primary_mobile": "+998907777777",  
      "full_name": "Alik"         
    }
```

### ✅ Response Examples
### Success (200 OK) : 
```json:
    {
      "status": "success",
      "message": "Verification code sent to your mobile number.",
      "expiry": "5 minutes"
    }
```

### Warning (400 Bad Request) :
```json:
    {
      "status": "warning",
      "message": "Missing required fields."
    }
```

### Error (500 Internal Server Error)
```json:
    {
      "status": "error",
      "message": "An unexpected error occurred. Please try again later."
    }
```

- Old OTPs are deleted every time SignUp is called
- OTP expiration: `5 minutes`
### Response format: 
```json:
    {
      "status": "success | warning | error",
      "message": "string",
      "expiry": "string (success holatda)"
    }
```
---

---


# 📌 POST /api/otp-verify/ 

- This endpoint is used to verify the OTP code sent to the user's phone number.
- Through this endpoint:
- If the phone number and OTP are correct, the user will be marked as phone_verified = `True`
- If the OTP is incorrect, expired, or the maximum number of attempts has been exceeded, an appropriate error message will be returned

---

---
### AllowAny (Can be used even by non-logged-in users), `request body`

```
{
  "primary_mobile": "string",   
  "otp_code": "string"          
}
```

### Response Examples `Success (200 OK)`
```{
  "status": "success",
  "message": "Mobile number verified successfully"
}
```

### Warning `(400 Bad Request)`
```
{
  "status": "warning",
  "message": "Missing required fields."
}
```


### Error (400 / 403)`OTP expired`
```{
  "status": "error",
  "message": "The verification code has expired. Please request a new one."
}
```

### Incorrect OTP
```
{
  "status": "error",
  "message": "The verification code is incorrect. You have 2 attempts left."
}
```


### Too many attempts (blocked)
```{
  "status": "error",
  "message": "Too many failed attempts. Try again later."
}
```


### User not found
```{
  "status": "error",
  "message": "No account was found with the provided information."
}
```
- OTP validity period: `5 minutes`
- Maxsimum attempts: `5`
- Block duration: `10 minutes`

### Response format:
```{
  "status": "success | warning | error",
  "message": "string"
}
```

------

------


# POST /api/register-owner/ #
Assigns a user as Account Owner and updates user details. Only authorized users can call.

---
### Request Body: `Example:`
```json
{
  "primary_mobile": "+201234567890",
  "username": "Ahmed Ali",
  "email": "ahmed@example.com",
  "password": "StrongPass123"
}
```

### Responses, Success
```jsoN
{
  "status": "success",
  "message": "You have been assigned the role of Account Owner."
}
```


### Error – User not found
```json
{
  "status": "error",
  "message": "No account was found with the provided information."
}
```
HTTP Status: 400 Bad Request

### Error – Invalid invite link
```json
{
  "status": "error",
  "message": "The invitation link is invalid or has expired."
}
```
HTTP Status: 400 Bad Request


### Error – System error
```json
{
  "status": "error",
  "message": "An unexpected error occurred. Please try again later."
}
```
### HTTP Status: `500 Internal Server Error`


***Notes*** 
- `OTP` must be verified before assigning user as `Account Owner`
- Only users with proper permissions can call this endpoint
- All messages are standardized via `SUCCESS_MESSAGES and ERROR_MESSAGES`
---

---

# accounts/ user/<int:user_id>/change-role/ [name='change_user_role'] #
# Description
Changes the role of a user based on role hierarchy rules.
Only authenticated users with sufficient privileges can perform this action.
All role changes are recorded in the audit log.

`Request Body` 
```
{
  "new_role": "manager"
}

```
### Allowed Values for new_role
account_owner
- admin
- manager
- employee

Permission Rules
A user can only change the role of users with a lower role.
A user cannot assign a role equal to or higher than their own.
Employees cannot change roles.

Success Response
```
{
  "msg": "User role has been successfully changed"
}

```


Returned when the request data is invalid.

```
{
  "error": "new_role is required"
}
```

```
{
  "error": "Invalid role"
}
```

401 Unauthorized

Returned when authentication credentials are missing or invalid.

```
{
  "detail": "Authentication credentials were not provided."
}
```

403 Forbidden

Returned when the user does not have permission to change the role.

```
{
  "error": "You do not have permission to change this user's role"
}
```

404 Not Found

Returned when the target user does not exist.

```
{
  "detail": "Not found."
}
```

Business Logic

The role change logic is handled in the service layer:

Validates role hierarchy

Prevents unauthorized role escalation

Updates the user role

Writes an audit log entry

- Notes.

   - Only authenticated users can access this endpoint

   - Role changes follow strict hierarchy validation

   - Designed using a clean separation of concerns (View + Service)




---

---


## 🔄 Resend OTP API

### Purpose
Foydalanuvchi telefon raqamiga yuborilgan OTP muddati tugagan yoki yo‘qolgan holatlarda qayta OTP kod yuborish.

---

## 🔄 Resend OTP API

### Purpose
Allows a user to request a new OTP code if the previous one has expired or was not received.

---

### 📌 Endpoint
`POST /api/auth/resend-otp/`

---

### 🔐 Permissions
- Public access (AllowAny)
- Only available for users who are already registered via OTP but not yet fully verified

---

### 📥 Request Body (JSON)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `primary_mobile` | string | ✔ | User mobile number |
| `cf_turnstile_response` | string | ✔ | Cloudflare human verification token |

**Example Request**
```json
{
  "primary_mobile": "+998901234567",
  "cf_turnstile_response": "token_xxx"
}
```

### ✅ Success Response
- Status: `200 OK`
- Returned when a new OTP is successfully generated and sent.

```{
  "status": "success",
  "message": "Verification code sent to your mobile number.",
  "expiry": "5 minutes"
}
```

### ⚠️ Error Responses
- Human verification failed
- Status: `400 Bad Request`
```
{
  "status": "error",
  "message": "An unexpected error occurred. Please try again later."
}
```


### No user found for the provided mobile number
- Status: `404 Not Found`
```
{
  "status": "error",
  "message": "No account was found with the provided information."
}
```

### 📝 Notes
- Any previously generated OTP will be deleted.
- A new OTP will be generated and assigned.
- OTP validity duration: 5 minutes
- In development mode, OTP is printed in the console for testing purposes.

---

---

# Session Test API

## Endpoint

**GET** `/accounts/session-test/`
This endpoint allows an **authenticated user** to check the expiration time of their JWT access token. It is intended for logged-in users only. Anonymous users or requests without a valid token will receive a `401 Unauthorized` response.

## Authentication
- **Required:** Yes  
- **Method:** JWT access token  
- **Header format:**  
Authorization: Bearer <access_token>

## Request
- **Method:** GET
- **Headers:**  
- `Authorization: Bearer <access_token>` (required)  
- `Accept: application/json` (recommended)
- **Body:** None

## Response

- **Success (200 OK)**  
Returns JSON with the username of the authenticated user and the token expiration datetime.

```json
{
    "user": "Husniddin",
    "token_expires_at": "2026-01-02T02:54:10"
}
```
- User: Username of the authenticated user
- token_expires_at: Expiration datetime of the JWT token in ISO 8601 format
- Error (401 Unauthorized)
- Returned if the request is made without a valid JWT token.

### Notes
- Only JWT-authenticated users can access this endpoint.
- This endpoint does not return any session data; it only checks the JWT token provided.
- The token_expires_at can be used to calculate how much time remains before the token becomes invalid


---

---

## 🔐 POST /auth/2fa-verify/

This endpoint is used to verify the Two-Factor Authentication (2FA) code after a successful login request where 2FA was required. Once verified, the user receives access and refresh tokens to complete authentication.

---

---

### 🧾 Request Body
```json
{
  "session_id": "uuid-from-login-response",
  "code": "123456"
}
```

| Field      | Type   | Required | Description                                                            |
| ---------- | ------ | -------- | ---------------------------------------------------------------------- |
| session_id | string | ✅ Yes    | Session ID returned from the login endpoint when 2FA was required      |
| code       | string | ✅ Yes    | 2FA verification code (generated by Authenticator App or sent via SMS) |

## Success Response (200)
Returned when the provided 2FA code is valid.
```{
  "access": "ACCESS_TOKEN",
  "refresh": "REFRESH_TOKEN",
  "message": "Login successful"
}
```

## Error Responses
Invalid or expired session
```
{
  "message": "No account was found with the provided information."
}
```

## Session expired
```
{
  "message": "The verification code has expired. Please request a new one."
}
```
## Incorrect 2FA code
```
{
  "message": "The verification code is incorrect. Please try again."
}

```
## SMS verification not implemented
```
{
  "message": "An unexpected error occurred. Please try again later."
}
```

## ***Notes***

- This endpoint is used ***only after login*** when:
  - The user has 2FA enabled
  - ogin API returns `2fa_required = true`
- `session_id must` be valid and not expired
- Supports:
  - Authenticator-based 2FA
  - SMS-based 2FA (implementation pending)


---

---

## POST /auth/2fa/verify-backup/
This endpoint allows a user to complete the login process using a 2FA Backup Code when they cannot access their authenticator app or SMS code.
A valid session_id must be obtained during the initial login request where 2FA was required.

## Request Body (JSON)
```
{
  "session_id": "uuid-from-login-response",
  "backup_code": "ABC123"
}
```
## Successful Response (200)

If the provided backup code is valid, the user is successfully authenticated and receives JWT tokens.
```
{
  "access": "ACCESS_TOKEN_HERE",
  "refresh": "REFRESH_TOKEN_HERE",
  "message": "Verification successful."
}
```
## Error Responses
- Invalid or Non-Existing Session
- Session not found or already verified.
```
{
  "message": "No account was found with the provided information."
}
```
## Expired Session

When the session has expired.
```
{
  "message": "The verification code has expired. Please request a new one."
}
```
## Incorrect Backup Code

When the backup code does not match any stored user codes.
```
{
  "message": "The verification code is incorrect. Please try again."
}
```
## Notes
- A backup code can be used only once
- Once verified, the backup code is automatically removed from the user’s available backup codes
- This endpoint does not send SMS or Email codes
- Requires a valid pending 2FA session

---

---

## PUT `/auth/2fa/enable/`

This endpoint allows an authenticated user to **enable Two-Factor Authentication (2FA)** on their account.  
Once enabled, the user will need 2FA verification during login, either via an **Authenticator App** or **SMS**.  
A set of **backup recovery codes** will also be generated for account recovery.

---

###  Authentication Required
Yes — User must be logged in.  
Include `Authorization: Bearer <access_token>` header.

---

### Request Body (JSON)
```json
{
  "two_fa_type": "AUTHENTICATOR"
}
```
or
```
{
  "two_fa_type": "SMS"
}
```
| Field       | Type   | Required | Description                                               |
| ----------- | ------ | -------- | --------------------------------------------------------- |
| two_fa_type | string | ✅ Yes    | Type of 2FA to enable. Accepted: `AUTHENTICATOR` or `SMS` |


## Success Response (200)

If 2FA is successfully enabled:
```
{
  "message": "Verification successful.",
  "backup_codes": [
    "KDJ29A",
    "PLM92X",
    "QWJ72S",
    "MNS82Q",
    "XKS77P"
  ]
}
```

message	Success message from SUCCESS_MESSAGES["VERIFICATION_ACCEPTED"]
backup_codes	List of one-time use backup recovery codes generated for the user

## Error Responses
 Unauthorized (User not logged in)
```
{
  "detail": "Authentication credentials were not provided."
}
```
## Validation Error / Unexpected Error
```
{
  "message": "An unexpected error occurred. Please try again later."
}
```

Uses ERROR_MESSAGES["SYSTEM_ERROR"] from manager’s standard messages.

## Notes

- Only authenticated users can enable 2FA.
- Backup codes are one-time use and should be securely stored by the user.
- After enabling 2FA, login will require verification with the selected 2FA method.
- Any validation errors or unexpected issues are returned with standard SYSTEM_ERROR message.

---

---

## 🔄 POST `/auth/token/refresh/`

This endpoint allows users to **refresh their access token** using a valid refresh token.  
It returns a new access token if the provided refresh token is valid.

---

### 📥 Request Body (JSON)
```json
{
  "refresh": "REFRESH_TOKEN_HERE"
}
```

| Field   | Type   | Required | Description                                 |
| ------- | ------ | -------- | ------------------------------------------- |
| refresh | string | ✅ Yes    | The valid refresh token issued during login |

## Success Response (200)
```
{
  "access": "NEW_ACCESS_TOKEN_HERE"
}
```

## Error Responses
Invalid / Expired Refresh Token
```
{
  "message": "An unexpected error occurred. Please try again later."
}
```
## Notes
- Users must provide a valid refresh token.
- If the refresh token is invalid or expired, the request will fail with a SYSTEM_ERROR message.
- No new refresh token is issued; only a new access token is returned.

---

---

## 🔒 POST `/auth/logout/`

This endpoint logs out the authenticated user by **blacklisting the provided refresh token**.

---

### 🔑 Authentication Required
Yes — User must be logged in.  
Include `Authorization: Bearer <access_token>` header.

---

### 📥 Request Body (JSON)
```json
{
  "refresh": "REFRESH_TOKEN_HERE"
}
```

## Success Response (205)
```
{
  "message": "You have logged out successfully."
}
```
### Uses SUCCESS_MESSAGES["LOGGED_OUT"].

### Error Responses
-Missing or Invalid Refresh Token
```{
  "message": "An unexpected error occurred. Please try again later."
}
```
- Uses ERROR_MESSAGES["SYSTEM_ERROR"].

### Notes
- Refresh token is blacklisted, so it cannot be used to generate new access tokens.
- User must provide a valid refresh token.
- Only authenticated users can log out.