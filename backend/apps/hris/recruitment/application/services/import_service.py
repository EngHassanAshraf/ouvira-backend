"""
ImportService — bulk import candidates from Excel/CSV files.
"""
import csv
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

from django.db import transaction

from ...models import Candidate, JobApplication, JobAdvertisement

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_ROWS = 1000
ALLOWED_EXTENSIONS = {".xlsx", ".csv"}


@dataclass
class ImportError:
    row: int
    error: str


@dataclass
class ImportSummary:
    added: int = 0
    shortlist_1: int = 0
    shortlist_2: int = 0
    rejected: int = 0
    errors: List[ImportError] = field(default_factory=list)
    imported_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


class ImportService:

    @staticmethod
    def import_cvs(file, job_advertisement_id, company_id, user) -> ImportSummary:
        """
        Parse file, validate, create Candidates + JobApplications.
        Returns ImportSummary with counts and per-row errors.
        """
        summary = ImportSummary()

        # 1. Validate file
        filename = getattr(file, 'name', '')
        ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}")

        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > MAX_FILE_SIZE:
            raise ValueError(f"File too large ({size} bytes). Max {MAX_FILE_SIZE} bytes.")

        # 2. Validate job advertisement
        try:
            ad = JobAdvertisement.objects.select_related("hiring_request__company").get(
                pk=job_advertisement_id,
                hiring_request__company_id=company_id,
            )
        except JobAdvertisement.DoesNotExist:
            raise ValueError(f"Job advertisement {job_advertisement_id} not found in your company.")

        # 3. Parse rows
        try:
            rows = ImportService._parse_file(file, ext)
        except Exception as e:
            raise ValueError(f"Failed to parse file: {e}")

        if len(rows) > MAX_ROWS:
            raise ValueError(f"File has {len(rows)} rows. Max {MAX_ROWS} rows allowed.")

        # 4. Process rows
        for i, row in enumerate(rows, start=2):  # row 1 = header
            try:
                ImportService._process_row(row, i, ad, company_id, summary)
            except Exception as e:
                summary.errors.append(ImportError(row=i, error=str(e)))

        return summary

    @staticmethod
    def _parse_file(file, ext) -> list:
        if ext == ".csv":
            content = file.read().decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(content))
            return list(reader)
        else:  # .xlsx
            try:
                import openpyxl
            except ImportError:
                raise ImportError("openpyxl is required for Excel import. Run: pip install openpyxl")
            wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                return []
            headers = [str(h).strip().lower() if h else "" for h in rows[0]]
            result = []
            for row in rows[1:]:
                result.append({headers[j]: (str(v).strip() if v is not None else "") for j, v in enumerate(row)})
            return result

    @staticmethod
    @transaction.atomic
    def _process_row(row, row_num, ad, company_id, summary: ImportSummary):
        # Normalise keys
        row = {k.strip().lower(): v for k, v in row.items()}

        # Extract name
        email = row.get("email", "").strip()
        if not email:
            raise ValueError("Missing required field: email")

        first_name = row.get("first_name") or row.get("name", "").split()[0] if row.get("name") else ""
        last_name = row.get("last_name") or (" ".join(row.get("name", "").split()[1:]) if row.get("name") else "")
        first_name = first_name.strip()
        last_name = last_name.strip()

        if not first_name:
            raise ValueError("Missing required field: first_name or name")

        # Get or create candidate
        candidate, _ = Candidate.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name or first_name,
                "phone": row.get("phone", ""),
                "linkedin_url": row.get("linkedin_url", "") or None,
                "source": row.get("source", "import"),
                "company_id": company_id,
            },
        )

        # Map classification
        classification = ImportService._map_classification(row.get("classification", ""))

        # Get or create application (skip duplicates)
        _, created = JobApplication.objects.get_or_create(
            candidate=candidate,
            job_advertisement=ad,
            defaults={
                "status": JobApplication.AppStatus.APPLIED,
                "classification": classification,
            },
        )

        if created:
            summary.added += 1
            if classification == JobApplication.Classification.SHORTLIST_1:
                summary.shortlist_1 += 1
            elif classification == JobApplication.Classification.SHORTLIST_2:
                summary.shortlist_2 += 1
            elif classification == JobApplication.Classification.NONE:
                pass  # not counted separately

    @staticmethod
    def _map_classification(value: str) -> str:
        mapping = {
            "shortlist_1": JobApplication.Classification.SHORTLIST_1,
            "shortlist1": JobApplication.Classification.SHORTLIST_1,
            "shortlist 1": JobApplication.Classification.SHORTLIST_1,
            "shortlist_2": JobApplication.Classification.SHORTLIST_2,
            "shortlist2": JobApplication.Classification.SHORTLIST_2,
            "shortlist 2": JobApplication.Classification.SHORTLIST_2,
            "rejected": "rejected",
        }
        return mapping.get(str(value).strip().lower(), JobApplication.Classification.NONE)
