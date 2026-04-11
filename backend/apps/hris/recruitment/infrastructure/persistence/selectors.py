"""
selectors.py — Persistence Layer
---------------------------------
Centralises complex, reusable QuerySets for the Recruitment module.

Rules:
  - NO business logic here — only data retrieval.
  - ViewSets call these selectors instead of building querysets inline.
  - Services call these selectors when they need rich, pre-fetched objects.
"""

from ...models import (
    HiringRequest,
    JobAdvertisement,
    Candidate,
    JobApplication,
    Interview,
    CandidateDocument,
    JobOffer,
)


# ─── Hiring Request ────────────────────────────────────────────────────────────

def get_hiring_requests_for_company(company_id, filters=None):
    qs = (
        HiringRequest.objects.filter(company_id=company_id)
        .select_related("job_title", "department", "created_by")
        .prefetch_related("approvals")
        .order_by("-created_at")
    )
    if filters:
        if filters.get("department"):
            qs = qs.filter(department_id=filters["department"])
        if filters.get("status"):
            qs = qs.filter(status=filters["status"])
        if filters.get("job_title"):
            qs = qs.filter(job_title_id=filters["job_title"])
        if filters.get("created_by"):
            qs = qs.filter(created_by_id=filters["created_by"])
    return qs


def get_hiring_request_by_id(request_id):
    return (
        HiringRequest.objects.select_related("job_title", "department", "created_by")
        .prefetch_related("approvals")
        .get(id=request_id)
    )


# ─── Job Advertisement ─────────────────────────────────────────────────────────

def get_advertisements_for_company(company_id, status=None, filters=None):
    qs = JobAdvertisement.objects.filter(
        hiring_request__company_id=company_id
    ).select_related("hiring_request__job_title", "hiring_request__department")
    if status:
        qs = qs.filter(status=status)
    if filters:
        if filters.get("status"):
            qs = qs.filter(status=filters["status"])
        if filters.get("city"):
            qs = qs.filter(city__icontains=filters["city"])
        if filters.get("area"):
            qs = qs.filter(area__icontains=filters["area"])
        if filters.get("platforms"):
            qs = qs.filter(platforms__contains=filters["platforms"])
        if filters.get("deadline_before"):
            qs = qs.filter(deadline__lte=filters["deadline_before"])
        if filters.get("deadline_after"):
            qs = qs.filter(deadline__gte=filters["deadline_after"])
    return qs.order_by("-created_at")


# ─── Candidate ─────────────────────────────────────────────────────────────────

def get_candidates_for_company(company_id, search=None):
    qs = Candidate.objects.filter(company_id=company_id)
    if search:
        qs = qs.filter(
            first_name__icontains=search
        ) | qs.filter(last_name__icontains=search) | qs.filter(email__icontains=search)
    return qs.order_by("last_name", "first_name")


# ─── Job Application (Pipeline / Kanban) ───────────────────────────────────────

def get_applications_for_advertisement(advertisement_id):
    """Returns all applications for a single job ad — used for the Kanban board."""
    return (
        JobApplication.objects.filter(job_advertisement_id=advertisement_id)
        .select_related("candidate", "job_advertisement")
        .order_by("-applied_at")
    )


def get_applications_for_company(company_id, status=None, filters=None):
    qs = JobApplication.objects.filter(
        candidate__company_id=company_id
    ).select_related("candidate", "job_advertisement")
    if status:
        qs = qs.filter(status=status)
    if filters:
        if filters.get("status"):
            qs = qs.filter(status=filters["status"])
        if filters.get("classification"):
            qs = qs.filter(classification=filters["classification"])
        if filters.get("job_board"):
            qs = qs.filter(job_board=filters["job_board"])
        if filters.get("job_advertisement"):
            qs = qs.filter(job_advertisement_id=filters["job_advertisement"])
        if filters.get("candidate"):
            qs = qs.filter(candidate_id=filters["candidate"])
    return qs.order_by("-applied_at")


# ─── Interview ─────────────────────────────────────────────────────────────────

def get_interviews_for_application(application_id):
    return (
        Interview.objects.filter(application_id=application_id)
        .select_related("application__candidate")
        .prefetch_related("interviewers")
        .order_by("interview_date")
    )


# ─── Candidate Documents ───────────────────────────────────────────────────────

def get_documents_for_candidate(candidate_id):
    return CandidateDocument.objects.filter(candidate_id=candidate_id).order_by("doc_type")


# ─── Job Offer ─────────────────────────────────────────────────────────────────

def get_offers_for_company(company_id):
    return (
        JobOffer.objects.filter(application__candidate__company_id=company_id)
        .select_related("application__candidate", "application__job_advertisement")
        .order_by("-created_at")
    )
