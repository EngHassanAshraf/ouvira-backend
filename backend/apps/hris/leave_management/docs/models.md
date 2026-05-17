# Models / Modellar

## Overview / Umumiy

**EN:** The Leave Management module consists of 5 models.  
**UZ:** Leave Management moduli 5 ta modeldan iborat.

---

## 1. LeaveType

**EN:** Defines the types of leave available in the system (KSA Labor Law).  
**UZ:** Tizimda mavjud ta'til turlarini belgilaydi (KSA Mehnat Qonuni).

| Field | Type | Description (EN) | Tavsif (UZ) |
|---|---|---|---|
| `name` | CharField | Leave type name | Ta'til turi nomi |
| `code` | SlugField | Unique code | Unikal kod |
| `days_per_year` | IntegerField | Default days per year | Yiliga standart kunlar |
| `is_active` | BooleanField | Active status | Faollik holati |

---

## 2. LeaveRequest

**EN:** Represents an employee's leave request with 2-stage approval.  
**UZ:** Xodimning 2 bosqichli tasdiqlash bilan ta'til so'rovini ifodalaydi.

| Field | Type | Description (EN) | Tavsif (UZ) |
|---|---|---|---|
| `employee` | FK → Employee | Request owner | So'rov egasi |
| `leave_type` | FK → LeaveType | Type of leave | Ta'til turi |
| `start_date` | DateField | Start date | Boshlanish sanasi |
| `end_date` | DateField | End date | Tugash sanasi |
| `duration` | IntegerField | Auto-calculated days | Avtomatik hisoblangan kunlar |
| `details` | TextField | Optional details (max 1000) | Ixtiyoriy tafsilot |
| `attachment` | FileField | PDF/JPG/PNG/DOCX max 5MB | Fayl ilova |
| `status` | CharField | Current status | Joriy holat |
| `created_by` | FK → Employee | Manager on behalf | Menejer nomidan |
| `manager_approved_by` | FK → Employee | Stage 1 approver | 1-bosqich tasdiqlovchi |
| `manager_approved_at` | DateTimeField | Stage 1 timestamp | 1-bosqich vaqti |
| `hr_approved_by` | FK → Employee | Stage 2 approver | 2-bosqich tasdiqlovchi |
| `hr_approved_at` | DateTimeField | Stage 2 timestamp | 2-bosqich vaqti |
| `declined_by` | FK → Employee | Who declined | Rad etgan |
| `declined_at` | DateTimeField | Decline timestamp | Rad etish vaqti |
| `decline_reason` | TextField | Reason for decline | Rad etish sababi |
| `interrupted_by` | FK → Employee | Who interrupted | To'xtatgan |
| `interruption_date` | DateField | Interruption date | To'xtatish sanasi |
| `cancelled_at` | DateTimeField | Cancel timestamp | Bekor qilish vaqti |

**Status choices:**

| Status | EN | UZ |
|---|---|---|
| `pending` | Pending | Kutilmoqda |
| `manager_approved` | Manager Approved | Menejer tasdiqladi |
| `approved` | Approved | Tasdiqlandi |
| `declined` | Declined | Rad etildi |
| `cancelled` | Cancelled | Bekor qilindi |
| `interrupted` | Interrupted | To'xtatildi |

---

## 3. LeaveBalance

**EN:** Tracks annual leave balance per employee per leave type.  
**UZ:** Har xodim uchun har ta'til turi bo'yicha yillik balansni kuzatadi.

| Field | Type | Description (EN) | Tavsif (UZ) |
|---|---|---|---|
| `employee` | FK → Employee | Balance owner | Balans egasi |
| `leave_type` | FK → LeaveType | Leave type | Ta'til turi |
| `year` | IntegerField | Year | Yil |
| `total_days` | DecimalField | Total allocated days | Jami ajratilgan kunlar |
| `used_days` | DecimalField | Used days | Ishlatilgan kunlar |
| `adjusted_days` | DecimalField | +/- manual adjustment | +/- qo'lda o'zgartirish |

**Computed property:**
```python
remaining_days = total_days + adjusted_days - used_days
```

---

## 4. LeaveBalanceAdjustment

**EN:** Audit trail for manual balance adjustments by managers.  
**UZ:** Menejerlar tomonidan qo'lda o'zgartirilgan balans tarixi.

| Field | Type | Description (EN) | Tavsif (UZ) |
|---|---|---|---|
| `balance` | FK → LeaveBalance | Related balance | Bog'liq balans |
| `adjusted_by` | FK → Employee | Who adjusted | Kim o'zgartirdi |
| `days` | DecimalField | +/- days | +/- kunlar |
| `justification` | TextField | Mandatory reason | Majburiy sabab |

---

## 5. LeaveActivityLog

**EN:** Records all actions performed on leave requests.  
**UZ:** Ta'til so'rovlariga oid barcha amallarni qayd etadi.

| Field | Type | Description (EN) | Tavsif (UZ) |
|---|---|---|---|
| `leave_request` | FK → LeaveRequest | Related request | Bog'liq so'rov |
| `performed_by` | FK → Employee | Who performed | Kim bajardi |
| `action` | CharField | Action type | Amal turi |
| `note` | TextField | Optional note | Ixtiyoriy izoh |

**Action choices:**

| Action | EN | UZ |
|---|---|---|
| `submitted` | Submitted | Yuborildi |
| `updated` | Updated | Yangilandi |
| `approved` | Approved | Tasdiqlandi |
| `declined` | Declined | Rad etildi |
| `cancelled` | Cancelled | Bekor qilindi |
| `interrupted` | Interrupted | To'xtatildi |
| `viewed` | Viewed | Ko'rildi |
| `deleted` | Deleted | O'chirildi |