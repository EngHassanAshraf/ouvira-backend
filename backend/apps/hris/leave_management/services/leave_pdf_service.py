import os
import logging
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.units import cm

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# Font fayllari joylashuvi
FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")
FONT_REGULAR = os.path.join(FONTS_DIR, "NotoSansArabic-Regular.ttf")
FONT_BOLD = os.path.join(FONTS_DIR, "NotoSansArabic-Bold.ttf")


class LeavePDFFontError(Exception):
    """Font topilmasa yoki yuklanmasa chiqariladigan xatolik."""
    pass


def _register_fonts():
    """
    Fontlarni ReportLab ga ro'yxatdan o'tkazish.
    Font fayli yo'q bo'lsa LeavePDFFontError beradi.
    """
    try:
        if not os.path.exists(FONT_REGULAR):
            raise LeavePDFFontError(
                f"Font topilmadi: {FONT_REGULAR}. "
                "fonts/README.md ga qarang."
            )
        if not os.path.exists(FONT_BOLD):
            raise LeavePDFFontError(
                f"Font topilmadi: {FONT_BOLD}. "
                "fonts/README.md ga qarang."
            )

        pdfmetrics.registerFont(TTFont("NotoArabic", FONT_REGULAR))
        pdfmetrics.registerFont(TTFont("NotoArabic-Bold", FONT_BOLD))
        logger.info("PDF fontlari muvaffaqiyatli yuklandi.")

    except LeavePDFFontError:
        raise
    except Exception as e:
        logger.exception("Font yuklashda kutilmagan xatolik.")
        raise LeavePDFFontError(f"Font yuklashda xatolik: {str(e)}")


class LeavePDFService:

    @staticmethod
    def _draw_header(c: canvas.Canvas, width: float, height: float, company_name: str):
        """
        PDF yuqori qismi — header.
        Chapda kompaniya nomi, o'rtada sarlavha AR+EN, o'ngda sana.
        """
        # --- Ajratuvchi chiziq ---
        c.setStrokeColor(colors.HexColor("#1a7a4a"))
        c.setLineWidth(2)
        c.line(2*cm, height - 3*cm, width - 2*cm, height - 3*cm)

        # --- Chapda kompaniya nomi ---
        c.setFont("NotoArabic-Bold", 14)
        c.setFillColor(colors.HexColor("#1a7a4a"))
        c.drawString(2*cm, height - 2.5*cm, company_name)

        # --- O'rtada sarlavha (AR + EN) ---
        c.setFont("NotoArabic-Bold", 16)
        c.setFillColor(colors.black)
        c.drawCentredString(width / 2, height - 2*cm, "Leave Request / طلب إجازة")

        # --- O'ngda sana ---
        from django.utils import timezone
        c.setFont("NotoArabic", 10)
        c.setFillColor(colors.grey)
        c.drawRightString(width - 2*cm, height - 2.5*cm, timezone.now().strftime("%d/%m/%Y"))


    @staticmethod
    def _draw_employee_info(c: canvas.Canvas, width: float, height: float, employee):
        """
        Xodim ma'lumotlari bo'limi.
        Ism, lavozim, bo'lim, xodim ID.
        """
        y = height - 4 * cm

        # --- Bo'lim sarlavhasi ---
        c.setFont("NotoArabic-Bold", 12)
        c.setFillColor(colors.HexColor("#1a7a4a"))
        c.drawString(2 * cm, y, "Employee Information / معلومات الموظف")

        # --- Ajratuvchi chiziq ---
        y -= 0.5 * cm
        c.setStrokeColor(colors.HexColor("#1a7a4a"))
        c.setLineWidth(0.5)
        c.line(2 * cm, y, width - 2 * cm, y)

        # --- Ma'lumotlar ---
        y -= 0.8 * cm
        c.setFont("NotoArabic", 11)
        c.setFillColor(colors.black)

        fields = [
            ("Employee Name / اسم الموظف", f"{employee.first_name} {employee.last_name}"),
            ("Employee ID / رقم الموظف", str(employee.id)),
            ("Department / القسم", str(employee.department) if employee.department else "-"),
            ("Position / المسمى الوظيفي", str(employee.position) if hasattr(employee, "position") else "-"),
        ]

        for label, value in fields:
            c.setFont("NotoArabic-Bold", 10)
            c.setFillColor(colors.grey)
            c.drawString(2 * cm, y, label)

            c.setFont("NotoArabic", 10)
            c.setFillColor(colors.black)
            c.drawString(9 * cm, y, value)
            y -= 0.7 * cm

        return y  # keyingi bo'lim uchun y qaytaramiz

    @staticmethod
    def _draw_leave_details(c: canvas.Canvas, width: float, height: float, leave_request, y: float):
        """
        Ta'til tafsilotlari bo'limi.
        Tur, boshlanish, tugash, davomiylik, status, tasdiqlagan.
        """
        # --- Bo'lim sarlavhasi ---
        y -= 0.5 * cm
        c.setFont("NotoArabic-Bold", 12)
        c.setFillColor(colors.HexColor("#1a7a4a"))
        c.drawString(2 * cm, y, "Leave Details / تفاصيل الإجازة")

        # --- Ajratuvchi chiziq ---
        y -= 0.5 * cm
        c.setStrokeColor(colors.HexColor("#1a7a4a"))
        c.setLineWidth(0.5)
        c.line(2 * cm, y, width - 2 * cm, y)

        # --- Ma'lumotlar ---
        y -= 0.8 * cm
        c.setFillColor(colors.black)

        fields = [
            ("Leave Type / نوع الإجازة", leave_request.leave_type.name),
            ("Start Date / تاريخ البداية", leave_request.start_date.strftime("%d/%m/%Y")),
            ("End Date / تاريخ النهاية", leave_request.end_date.strftime("%d/%m/%Y")),
            ("Duration / المدة", f"{leave_request.duration} days / أيام"),
            ("Status / الحالة", leave_request.get_status_display()),
            ("Approved By / معتمد من",
             f"{leave_request.hr_approved_by.first_name} {leave_request.hr_approved_by.last_name}" if leave_request.hr_approved_by else "-"),
            ("Approval Date / تاريخ الاعتماد",
             leave_request.hr_approved_at.strftime("%d/%m/%Y") if leave_request.hr_approved_at else "-"),
        ]

        for label, value in fields:
            c.setFont("NotoArabic-Bold", 10)
            c.setFillColor(colors.grey)
            c.drawString(2 * cm, y, label)

            c.setFont("NotoArabic", 10)
            c.setFillColor(colors.black)
            c.drawString(9 * cm, y, value)
            y -= 0.7 * cm

        return y

    @staticmethod
    def _draw_signatures(c: canvas.Canvas, width: float, height: float, y: float, leave_request_id):
        """
        Imzo qatorlari + footer.
        Xodim imzosi, Menejer imzosi, HR imzosi.
        """
        y -= 2 * cm

        # --- Imzo qatorlari ---
        signature_fields = [
            ("Employee / الموظف", 2 * cm),
            ("Manager / المدير", width / 2 - 2 * cm),
            ("HR Director / مدير الموارد البشرية", width - 6 * cm),
        ]

        for label, x in signature_fields:
            # Imzo chizig'i
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.5)
            c.line(x, y, x + 4 * cm, y)

            # Imzo label
            c.setFont("NotoArabic", 9)
            c.setFillColor(colors.grey)
            c.drawString(x, y - 0.5 * cm, label)

        # --- Footer ---
        c.setStrokeColor(colors.HexColor("#1a7a4a"))
        c.setLineWidth(1)
        c.line(2 * cm, 2 * cm, width - 2 * cm, 2 * cm)

        # Hujjat raqami
        c.setFont("NotoArabic", 8)
        c.setFillColor(colors.grey)
        c.drawString(2 * cm, 1.5 * cm, f"Doc No: LR-{leave_request_id}")

        # Sana
        from django.utils import timezone
        c.drawRightString(
            width - 2 * cm, 1.5 * cm,
            timezone.now().strftime("%d/%m/%Y %H:%M")
        )

    @staticmethod
    def generate(leave_request_id: int, company_name: str) -> BytesIO:
        """
        Asosiy metod — PDF yaratish.
        Faqat APPROVED so'rovlar uchun ishlaydi.
        BytesIO qaytaradi.
        """
        from apps.hris.leave_management.models import LeaveRequest

        # 1. So'rovni bazadan olamiz
        leave_request = LeaveRequest.objects.select_related(
            "employee", "leave_type",
            "hr_approved_by", "manager_approved_by",
            "employee__department",
        ).filter(id=leave_request_id, is_deleted=False).first()

        if not leave_request:
            raise ValueError("Leave request not found.")

        # 2. Faqat APPROVED tekshiruv
        if leave_request.status != LeaveRequest.StatusChoice.APPROVED:
            raise ValidationError("Only approved leave requests can be exported as PDF.")

        # 3. Fontlarni yuklash
        _register_fonts()

        # 4. PDF yaratish
        buffer = BytesIO()
        width, height = A4
        c = canvas.Canvas(buffer, pagesize=A4)

        # 5. Barcha bo'limlarni chizish
        LeavePDFService._draw_header(c, width, height, company_name)

        y = LeavePDFService._draw_employee_info(
            c, width, height, leave_request.employee
        )
        y = LeavePDFService._draw_leave_details(
            c, width, height, leave_request, y
        )
        LeavePDFService._draw_signatures(
            c, width, height, y, leave_request_id
        )

        # 6. PDF ni saqlash
        c.save()
        buffer.seek(0)

        logger.info(f"PDF yaratildi: leave_request_id={leave_request_id}")
        return buffer