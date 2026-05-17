# Services / Servislar

## Overview / Umumiy

**EN:** The Leave Management module has 3 service classes, each responsible for a specific domain of business logic.  
**UZ:** Leave Management moduli 3 ta servis klassiga ega, har biri o'z biznes logikasiga mas'ul.

```
services/
├── leave_request_services.py    — So'rov yaratish, tahrirlash, bekor qilish
├── leave_approval_services.py   — Tasdiqlash, rad etish, to'xtatish
├── leave_balance_services.py    — Balans boshqaruvi
└── leave_pdf_service.py         — PDF export
```


---

## 1. LeaveRequestService

### `create_leave_request()`
**EN:** Creates a new leave request with full validation.  
**UZ:** To'liq validatsiya bilan yangi ta'til so'rovi yaratadi.

**Validatsiya tartibi:**
1. Leave type mavjud va aktiv
2. end_date >= start_date
3. start_date o'tmishda emas
4. Overlap tekshiruvi
5. Balans yetarliligi

---

### `update_leave_request()`
**EN:** Updates a leave request. Only allowed in `PENDING` status.  
**UZ:** Ta'til so'rovini yangilaydi. Faqat `PENDING` holatida ruxsat.

---

### `cancel_leave_request()`
**EN:** Cancels a leave request before start date. Refunds balance if status was `APPROVED`.  
**UZ:** Start date dan oldin so'rovni bekor qiladi. `APPROVED` bo'lsa balansni qaytaradi.

**Muhim:** APPROVED so'rov bekor qilinganda balans avtomatik qaytariladi.

---

## 2. LeaveApprovalService

### `manager_approve()`
**EN:** Stage 1 approval. `PENDING` → `MANAGER_APPROVED`.  
**UZ:** 1-bosqich tasdiqlash. `PENDING` → `MANAGER_APPROVED`.

---

### `hr_approve()`
**EN:** Stage 2 approval. `MANAGER_APPROVED` → `APPROVED`. Auto-deducts balance.  
**UZ:** 2-bosqich tasdiqlash. `MANAGER_APPROVED` → `APPROVED`. Balansni avtomatik ayiradi.

---

### `decline()`
**EN:** Declines a request at any stage. Reason is mandatory.  
**UZ:** Istalgan bosqichda rad etadi. Sabab majburiy.

---

### `interrupt()`
**EN:** Interrupts an ongoing approved leave. Refunds unused days.  
**UZ:** Davom etayotgan tasdiqlangan ta'tilni to'xtatadi. Ishlatilmagan kunlarni qaytaradi.

**Hisoblash:**
```python
used_days      = interruption_date - start_date
remaining_days = duration - used_days
# remaining_days balansga qaytariladi
```

---

### `bulk_approve()` / `bulk_decline()`
**EN:** Processes multiple requests at once. Returns success/failed lists.  
**UZ:** Bir vaqtda ko'p so'rovlarni qayta ishlaydi. Muvaffaqiyatli/muvaffaqiyatsiz ro'yxat qaytaradi.

**Response format:**
```python
# bulk_approve
{"approved": [1, 2, 3], "failed": [{"id": 4, "error": "..."}]}

# bulk_decline
{"declined": [1, 2, 3], "failed": [{"id": 4, "error": "..."}]}
```

---

## 3. LeaveBalanceService

### `initialize_balance()`
**EN:** Creates initial balance for an employee. Called at year start or when new employee joins.  
**UZ:** Xodim uchun boshlang'ich balans yaratadi. Yil boshida yoki yangi xodim qo'shilganda chaqiriladi.

---

### `deduct_balance()`
**EN:** Deducts days from balance. Called automatically on HR approval.  
**UZ:** Balansdan kunlar ayiradi. HR tasdiqlashida avtomatik chaqiriladi.

---

### `refund_balance()`
**EN:** Refunds days to balance. Called on cancellation or interruption.  
**UZ:** Balansga kunlar qaytaradi. Bekor qilish yoki to'xtatishda chaqiriladi.

---

### `adjust_balance()`
**EN:** Manual +/- adjustment by manager. Justification is mandatory. Creates audit record.  
**UZ:** Menejer tomonidan qo'lda +/- o'zgartirish. Sabab majburiy. Audit yozuvi yaratadi.

---

### `get_balance_summary()`
**EN:** Returns all leave type balances for an employee for a given year.  
**UZ:** Xodimning berilgan yil uchun barcha ta'til turlari bo'yicha balansini qaytaradi.

**Response format:**
```python
[
    {
        "leave_type": "Annual Leave",
        "leave_type_code": "annual",
        "total_days": 21.0,
        "used_days": 5.0,
        "adjusted_days": 3.0,
        "remaining_days": 19.0,
    },
    ...
]
```

---

## 4. LeavePDFService

**EN:** Generates a PDF document for approved leave requests.  
**UZ:** Tasdiqlangan ta'til so'rovlari uchun PDF hujjat yaratadi.

### `generate()`
**EN:** Main method. Only works for `APPROVED` requests. Returns `BytesIO`.  
**UZ:** Asosiy metod. Faqat `APPROVED` so'rovlar uchun ishlaydi. `BytesIO` qaytaradi.

**PDF tarkibi:**
1. Header — kompaniya nomi, sarlavha, sana
2. Xodim ma'lumotlari
3. Ta'til tafsilotlari
4. Imzolar + footer

**Xatoliklar:**

| Error | Sabab |
|---|---|
| `LeavePDFFontError` | Font fayli topilmadi |
| `ValidationError` | So'rov APPROVED emas |
| `ValueError` | So'rov topilmadi |

---

## Service Interaction / Servislar o'zaro aloqasi



```
LeaveRequestService.create()
↓
LeaveApprovalService.manager_approve()
↓
LeaveApprovalService.hr_approve()
↓
LeaveBalanceService.deduct_balance()   ← avtomatik
↓
LeavePDFService.generate()             ← export uchun
```