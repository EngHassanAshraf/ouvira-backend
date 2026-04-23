# PDF Export

## Overview / Umumiy

**EN:** The PDF Export feature allows employees and managers to export 
approved leave requests as formatted PDF documents with Arabic (RTL) 
and English support.  
**UZ:** PDF Export funksiyasi xodimlar va menejerlar uchun tasdiqlangan 
ta'til so'rovlarini arabcha (RTL) va inglizcha qo'llab-quvvatlagan 
holda formatlangan PDF hujjat sifatida export qilish imkonini beradi.

---

## Requirements / Talablar

### Dependencies / Bog'liqliklar

| Package | Version | Purpose (EN) | Maqsad (UZ) |
|---|---|---|---|
| `reportlab` | 4.4.1 | PDF generation | PDF yaratish |
| `arabic-reshaper` | 3.0.0 | Arabic text shaping | Arabcha matn shakllantirish |
| `python-bidi` | 0.6.6 | RTL text support | RTL matn qo'llab-quvvatlash |

### Fonts / Fontlar

**EN:** Download and place fonts in `leave_management/fonts/`:  
**UZ:** Fontlarni yuklab `leave_management/fonts/` ga joylashtiring:



leave_management/fonts/<br>
├── NotoSansArabic-Regular.ttf<br>
└── NotoSansArabic-Bold.ttf


**Download:** https://fonts.google.com/noto/specimen/Noto+Sans+Arabic

> **EN:** Font files are listed in `.gitignore` and not tracked in the repository.  
> **UZ:** Font fayllari `.gitignore` da va repoga yuklanmaydi.

---

## PDF Structure / PDF tuzilmasi


```
┌─────────────────────────────────────┐
│  Company Name    Leave Request   Date│  ← Header
│  ─────────────────────────────────  │
│                                     │
│  Employee Information               │
│  ─────────────────────────────────  │
│  Name:        John Doe              │  ← Xodim ma'lumotlari
│  ID:          1234                  │
│  Department:  IT                    │
│  Position:    Developer             │
│                                     │
│  Leave Details                      │
│  ─────────────────────────────────  │
│  Leave Type:  Annual Leave          │
│  Start Date:  01/05/2026            │  ← Ta'til tafsilotlari
│  End Date:    10/05/2026            │
│  Duration:    10 days               │
│  Status:      Approved              │
│  Approved By: HR Manager            │
│                                     │
│  ____________  ____________  _____  │
│  Employee      Manager       HR     │  ← Imzolar
│  ─────────────────────────────────  │
│  Doc No: LR-1              Date     │  ← Footer
└─────────────────────────────────────┘
```


---

## API Endpoints / API endpointlari

### Employee / Xodim



GET /api/hris/leave/leave-requests/<pk>/export-pdf/

**EN:** Employee can only export their own approved requests.  
**UZ:** Xodim faqat o'zining tasdiqlangan so'rovini export qila oladi.

### Manager / Menejer

GET /api/hris/leave/manager/leave-requests/<pk>/export-pdf/

**EN:** Manager can export any employee's approved request.  
**UZ:** Menejer istalgan xodimning tasdiqlangan so'rovini export qila oladi.

---

## Response / Javob

**Success (200):**

Content-Type: application/pdf
Content-Disposition: attachment; filename="leave_request_<pk>.pdf"

**Errors / Xatoliklar:**

| Code | Reason (EN) | Sabab (UZ) |
|---|---|---|
| `400` | Request not approved | So'rov tasdiqlanmagan |
| `400` | Font files missing | Font fayllari yo'q |
| `404` | Request not found | So'rov topilmadi |
| `403` | Not authorized | Ruxsat yo'q |

---

## Error Handling / Xatoliklarni boshqarish

**EN:** If font files are missing, the service raises `LeavePDFFontError`.  
**UZ:** Font fayllari yo'q bo'lsa, servis `LeavePDFFontError` xatoligini chiqaradi.

```python
# Xatolik turlari
LeavePDFFontError  — Font topilmadi
ValidationError    — So'rov APPROVED emas
ValueError         — So'rov topilmadi
```

---

## Setup Guide / O'rnatish qo'llanmasi

**EN:** Follow these steps to set up PDF export:  
**UZ:** PDF export ni sozlash uchun quyidagi qadamlarni bajaring:

**1. Install dependencies / Bog'liqliklarni o'rnating:**
```bash
pip install reportlab==4.4.1 arabic-reshaper==3.0.0 python-bidi==0.6.6
```

**2. Download fonts / Fontlarni yuklab oling:**


https://fonts.google.com/noto/specimen/Noto+Sans+Arabic
**3. Place fonts / Fontlarni joylashtiring:**
```bash
cp NotoSansArabic-Regular.ttf backend/apps/hris/leave_management/fonts/
cp NotoSansArabic-Bold.ttf backend/apps/hris/leave_management/fonts/
```

**4. Test / Tekshiring:**
```bash
python manage.py test apps.hris.leave_management.tests.test_pdf_export
```