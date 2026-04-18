"""
Bulk employee operations:
  - BulkArchiveService  — soft-delete multiple employees at once
  - BulkRestoreService  — restore multiple archived employees at once
  - EmployeeImportService — import employees from an Excel (.xlsx) file
  - EmployeeExportService — export employees to CSV
"""
import csv
import io
import logging
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


# ── Bulk Archive ───────────────────────────────────────────────────────────────

class BulkArchiveService:

    @staticmethod
    @transaction.atomic
    def archive(company_id: int, employee_ids: list[int]) -> dict:
        """
        Soft-delete a list of employees belonging to company_id.
        Returns a summary: {archived: [...], not_found: [...]}.
        """
        from apps.hris.hris_core.models.employee import Employee

        now = timezone.now()
        qs = Employee.objects.filter(
            id__in=employee_ids,
            company_id=company_id,
            is_deleted=False,
        )
        found_ids = list(qs.values_list("id", flat=True))
        not_found = [eid for eid in employee_ids if eid not in found_ids]

        qs.update(is_deleted=True, deleted_at=now)

        logger.info(
            "Bulk archive: company=%s archived=%s not_found=%s",
            company_id, found_ids, not_found,
        )
        return {"archived": found_ids, "not_found": not_found}


# ── Bulk Restore ───────────────────────────────────────────────────────────────

class BulkRestoreService:

    @staticmethod
    @transaction.atomic
    def restore(company_id: int, employee_ids: list[int]) -> dict:
        """
        Restore a list of soft-deleted employees belonging to company_id.
        Returns a summary: {restored: [...], not_found: [...]}.
        """
        from apps.hris.hris_core.models.employee import Employee

        qs = Employee.all_objects.filter(
            id__in=employee_ids,
            company_id=company_id,
            is_deleted=True,
        )
        found_ids = list(qs.values_list("id", flat=True))
        not_found = [eid for eid in employee_ids if eid not in found_ids]

        qs.update(is_deleted=False, deleted_at=None)

        logger.info(
            "Bulk restore: company=%s restored=%s not_found=%s",
            company_id, found_ids, not_found,
        )
        return {"restored": found_ids, "not_found": not_found}


# ── Excel Import ───────────────────────────────────────────────────────────────

# Required columns in the uploaded Excel file (case-insensitive header match)
IMPORT_REQUIRED_COLUMNS = {"employee_id", "first_name", "last_name", "national_id"}

IMPORT_OPTIONAL_COLUMNS = {
    "nationality", "gender", "marital_status", "contact_number",
    "secondary_phone", "personal_email", "address",
    "passport_number", "visa_number", "fingerprint_id",
    "national_id_job_title", "national_id_status", "iqama_status",
}

ALL_IMPORT_COLUMNS = IMPORT_REQUIRED_COLUMNS | IMPORT_OPTIONAL_COLUMNS


class EmployeeImportService:

    @staticmethod
    def import_from_excel(company_id: int, file) -> dict:
        """
        Parse an Excel (.xlsx) file and create Employee records.

        Returns:
            {
                "added": <int>,
                "errors": [{"row": <n>, "employee_id": <str>, "error": <str>}, ...],
                "total_rows": <int>,
            }
        """
        try:
            import openpyxl
        except ImportError:
            raise RuntimeError(
                "openpyxl is required for Excel import. "
                "Add it to requirements.txt and rebuild."
            )

        from apps.hris.hris_core.models.employee import Employee

        wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
        ws = wb.active

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return {"added": 0, "errors": [], "total_rows": 0}

        # Normalise header row
        raw_headers = [str(h).strip().lower() if h else "" for h in rows[0]]
        data_rows = rows[1:]

        # Validate required columns
        missing = IMPORT_REQUIRED_COLUMNS - set(raw_headers)
        if missing:
            raise ValueError(
                f"Missing required columns: {', '.join(sorted(missing))}"
            )

        added = 0
        errors = []

        for row_num, row in enumerate(data_rows, start=2):
            row_dict = {
                raw_headers[i]: (str(cell).strip() if cell is not None else "")
                for i, cell in enumerate(row)
                if i < len(raw_headers)
            }

            employee_id_val = row_dict.get("employee_id", "")
            if not employee_id_val:
                errors.append({"row": row_num, "employee_id": "", "error": "employee_id is empty"})
                continue

            # Build kwargs — only include known columns
            kwargs = {
                col: row_dict[col]
                for col in ALL_IMPORT_COLUMNS
                if col in row_dict and row_dict[col]
            }

            # Validate national_id
            national_id = kwargs.get("national_id", "")
            if not national_id.isdigit() or len(national_id) != 10:
                errors.append({
                    "row": row_num,
                    "employee_id": employee_id_val,
                    "error": "national_id must be exactly 10 digits",
                })
                continue

            try:
                with transaction.atomic():
                    Employee.objects.create(company_id=company_id, **kwargs)
                added += 1
            except Exception as exc:
                errors.append({
                    "row": row_num,
                    "employee_id": employee_id_val,
                    "error": str(exc),
                })

        logger.info(
            "Employee import: company=%s added=%s errors=%s total=%s",
            company_id, added, len(errors), len(data_rows),
        )
        return {
            "added": added,
            "errors": errors,
            "total_rows": len(data_rows),
        }


# ── CSV Export ─────────────────────────────────────────────────────────────────

EXPORT_COLUMNS = [
    "employee_id", "first_name", "last_name", "nationality",
    "national_id", "passport_number", "visa_number", "fingerprint_id",
    "gender", "marital_status", "date_of_birth",
    "contact_number", "secondary_phone", "personal_email", "address",
    "national_id_status", "iqama_status",
    "department__name", "location__name",
]


class EmployeeExportService:

    @staticmethod
    def export_to_csv(company_id: int, filters: dict = None) -> io.StringIO:
        """
        Export active employees for a company to a CSV StringIO buffer.
        Accepts the same filter dict as apply_employee_filters.
        """
        from apps.hris.hris_core.selectors.employee_selectors import EmployeeSelector
        from apps.hris.hris_core.selectors.employee_filters import apply_employee_filters

        qs = EmployeeSelector.get_employee_by_company(company_id=company_id)
        if filters:
            qs = apply_employee_filters(qs, filters)

        # Flatten FK fields
        qs = qs.select_related("department", "location")

        buffer = io.StringIO()
        writer = csv.writer(buffer)

        # Header row — replace __ with . for readability
        writer.writerow([col.replace("__", ".") for col in EXPORT_COLUMNS])

        for emp in qs.iterator():
            row = []
            for col in EXPORT_COLUMNS:
                if "__" in col:
                    parts = col.split("__")
                    val = emp
                    for part in parts:
                        val = getattr(val, part, None)
                        if val is None:
                            break
                else:
                    val = getattr(emp, col, None)
                row.append("" if val is None else str(val))
            writer.writerow(row)

        buffer.seek(0)
        return buffer
