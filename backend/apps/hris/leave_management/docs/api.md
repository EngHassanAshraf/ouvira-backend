# API Endpoints

## Base URL

---

## Employee Endpoints / Xodim endpointlari

### 1. Leave Requests / Ta'til so'rovlari

| Method | URL | Description (EN) | Tavsif (UZ) |
|---|---|---|---|
| `GET` | `leave-requests/` | List all requests | Barcha so'rovlar ro'yxati |
| `POST` | `leave-requests/` | Create new request | Yangi so'rov yaratish |
| `GET` | `leave-requests/<pk>/` | Request detail | So'rov tafsiloti |
| `PATCH` | `leave-requests/<pk>/` | Update request | So'rovni tahrirlash |
| `POST` | `leave-requests/<pk>/cancel/` | Cancel request | So'rovni bekor qilish |
| `GET` | `leave-requests/<pk>/export-pdf/` | Export as PDF | PDF ga export |

### Query Parameters / So'rov parametrlari

**GET** `leave-requests/`

| Parameter | Type | Description (EN) | Tavsif (UZ) |
|---|---|---|---|
| `status` | string | Filter by status | Status bo'yicha filter |
| `leave_type_id` | int (multi) | Filter by leave type | Ta'til turi bo'yicha filter |
| `start_date` | date | Filter from date | Sanadan filter |
| `end_date` | date | Filter to date | Sanagacha filter |
| `duration_min` | int | Min duration | Minimal davomiylik |
| `duration_max` | int | Max duration | Maksimal davomiylik |
| `ordering` | string | Sort field | Saralash maydoni |

**Ordering options:**


leave_type__name, -leave_type__name<br>
start_date, -start_date<br>
end_date, -end_date<br>
duration, -duration<br>
status, -status<br>
created_at, -created_at<br>


### Request Body / So'rov tanasi

**POST** `leave-requests/`
```json
{
    "leave_type": 1,
    "start_date": "2026-05-01",
    "end_date": "2026-05-10",
    "details": "Annual vacation",
    "attachment": "<file>"
}
```

---

### 2. Leave Balance / Ta'til balansi

| Method | URL | Description (EN) | Tavsif (UZ) |
|---|---|---|---|
| `GET` | `balance/` | My balance summary | Mening balansim |

**Query Parameters:**

| Parameter | Type | Description (EN) | Tavsif (UZ) |
|---|---|---|---|
| `year` | int | Filter by year | Yil bo'yicha filter |

---

### 3. Activity Log / Amallar tarixi

| Method | URL | Description (EN) | Tavsif (UZ) |
|---|---|---|---|
| `GET` | `activity-logs/` | View activity logs | Amallar tarixini ko'rish |

**Query Parameters:**

| Parameter | Type | Description (EN) | Tavsif (UZ) |
|---|---|---|---|
| `leave_request_id` | int | Filter by request | So'rov bo'yicha filter |
| `action` | string | Filter by action | Amal bo'yicha filter |

---

## Manager Endpoints / Menejer endpointlari

### 1. Leave Requests / Ta'til so'rovlari

| Method | URL | Description (EN) | Tavsif (UZ) |
|---|---|---|---|
| `GET` | `manager/leave-requests/` | All company requests | Kompaniya so'rovlari |
| `POST` | `manager/leave-requests/<pk>/approve/` | Stage 1 approve | 1-bosqich tasdiqlash |
| `POST` | `manager/leave-requests/<pk>/hr-approve/` | Stage 2 approve | 2-bosqich tasdiqlash |
| `POST` | `manager/leave-requests/<pk>/decline/` | Decline request | Rad etish |
| `POST` | `manager/leave-requests/<pk>/interrupt/` | Interrupt leave | Ta'tilni to'xtatish |
| `POST` | `manager/leave-requests/bulk-approve/` | Bulk approve | Ommaviy tasdiqlash |
| `POST` | `manager/leave-requests/bulk-decline/` | Bulk decline | Ommaviy rad etish |
| `GET` | `manager/leave-requests/<pk>/export-pdf/` | Export as PDF | PDF ga export |

### Request Bodies / So'rov tanalari

**POST** `manager/leave-requests/<pk>/decline/`
```json
{
    "reason": "Does not meet policy criteria."
}
```

**POST** `manager/leave-requests/<pk>/interrupt/`
```json
{
    "interruption_date": "2026-05-05"
}
```

**POST** `manager/leave-requests/bulk-approve/`
```json
{
    "leave_request_ids": [1, 2, 3]
}
```

**POST** `manager/leave-requests/bulk-decline/`
```json
{
    "leave_request_ids": [1, 2, 3],
    "reason": "Overlapping with project deadline."
}
```

---

### 2. Leave Balance / Ta'til balansi

| Method | URL | Description (EN) | Tavsif (UZ) |
|---|---|---|---|
| `GET` | `balance/manager/<employee_pk>/` | Employee balance | Xodim balansi |
| `POST` | `balance/adjust/<employee_pk>/` | Adjust balance | Balans o'zgartirish |
| `POST` | `balance/initialize/<employee_pk>/` | Initialize balance | Balans yaratish |

**POST** `balance/adjust/<employee_pk>/`
```json
{
    "leave_type_id": 1,
    "year": 2026,
    "days": 3.0,
    "justification": "Extra days granted for overtime."
}
```

---

## Validation Rules / Validatsiya qoidalari

| Field | Rule (EN) | Qoida (UZ) |
|---|---|---|
| `start_date` | Cannot be in the past | O'tmishda bo'lmasligi kerak |
| `end_date` | Must be >= start_date | start_date dan kichik bo'lmasligi kerak |
| `details` | Max 1000 characters | Maksimal 1000 belgi |
| `attachment` | PDF/JPG/PNG/DOCX, max 5MB | PDF/JPG/PNG/DOCX, maksimal 5MB |
| `overlap` | No overlapping requests | Ta'tillar kesishmasligi kerak |
| `balance` | Sufficient balance required | Yetarli balans bo'lishi kerak |
| `decline reason` | Required | Majburiy |
| `justification` | Required for adjustment | Balans o'zgartirishda majburiy |

---

## Response Codes / Javob kodlari

| Code | Description (EN) | Tavsif (UZ) |
|---|---|---|
| `200` | Success | Muvaffaqiyatli |
| `201` | Created | Yaratildi |
| `400` | Bad Request | Noto'g'ri so'rov |
| `401` | Unauthorized | Autentifikatsiya kerak |
| `403` | Forbidden | Ruxsat yo'q |
| `404` | Not Found | Topilmadi |