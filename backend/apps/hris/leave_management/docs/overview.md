# Leave Management Module / Ta'til Boshqaruvi Moduli

## Overview / Umumiy ma'lumot

**EN:** The Leave Management module handles all leave-related operations 
for employees and managers within the HRIS system. It supports a 
2-stage approval workflow, balance tracking, and PDF export.

**UZ:** Leave Management moduli HRIS tizimida xodimlar va menejerlar 
uchun barcha ta'tilga oid operatsiyalarni boshqaradi. 2 bosqichli 
tasdiqlash, balans kuzatuvi va PDF export qo'llab-quvvatlanadi.

---

## Module Structure / Modul tuzilmasi

leave_management/
├── models/              — Ma'lumotlar bazasi modellari
├── services/            — Biznes logika
├── selectors/           — Ma'lumot olish (queries)
├── api/
│   ├── views/           — API viewlar
│   ├── serializers.py   — Serializatorlar
│   └── urls.py          — URL marshrutlash
├── migrations/          — Migratsiyalar
├── fonts/               — PDF uchun fontlar
├── docs/                — Dokumentatsiya
└── tests.py             — Testlar

---

## Key Features / Asosiy imkoniyatlar

**EN:**
- Leave request creation, update, cancel
- 2-stage approval: Direct Manager → HR Director
- Automatic balance deduction on approval
- Balance refund on cancellation or interruption
- PDF export for approved requests
- Activity log for all actions
- Bulk approve / decline
- Advanced filtering and sorting

**UZ:**
- Ta'til so'rovi yaratish, tahrirlash, bekor qilish
- 2 bosqichli tasdiqlash: Menejer → HR Director
- Tasdiqlanganda balansdan avtomatik ayirish
- Bekor qilish yoki to'xtatishda balansni qaytarish
- Tasdiqlangan so'rovlarni PDF ga export qilish
- Barcha amallar uchun activity log
- Bulk approve / decline
- Kengaytirilgan filter va saralash

---

## Leave Types / Ta'til turlari

| Code | EN | UZ |
|---|---|---|
| `annual` | Annual Leave | Yillik ta'til |
| `sick` | Sick Leave | Kasallik ta'tili |
| `national_day` | National Day | Milliy bayram |
| `eid_fitr` | Eid Al-Fitr | Ro'za hayit |
| `eid_adha` | Eid Al-Adha | Qurbon hayit |
| `hajj` | Hajj Leave | Haj ta'tili |
| `maternity` | Maternity Leave | Tug'ruq ta'tili |
| `paternity` | Paternity Leave | Ota ta'tili |
| `bereavement` | Bereavement Leave | Motam ta'tili |
| `work_injury` | Work Injury Leave | Ishlab chiqarish jarohati |
| `exceptional` | Exceptional Leave | Favqulodda ta'til |

---

## Approval Workflow / Tasdiqlash jarayoni

Xodim so'rov yuboradi
↓
[PENDING]
↓
Direct Manager tasdiqlaydi
↓
[MANAGER_APPROVED]
↓
HR Director tasdiqlaydi
↓
[APPROVED]

**Rad etish** — istalgan bosqichda, reason majburiy → `[DECLINED]`  
**Bekor qilish** — start_date dan oldin → `[CANCELLED]`  
**To'xtatish** — ta'til davomida → `[INTERRUPTED]`

---

## Related Modules / Bog'liq modullar

| Modul | Bog'liqlik |
|---|---|
| `hris_core` | `Employee` modeli |
| `access_control` | `IsAdminUser` permission |
| `internal_auth` | `PermissionResolver` |
| `notifications` | ⏳ Keyinroq integratsiya |